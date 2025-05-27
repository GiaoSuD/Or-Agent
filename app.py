from flask import Flask, render_template_string, request
import requests
import json

app = Flask(__name__)

# URL API of the MCP server  
MCP_API_URL = "http://127.0.0.1:5050"

# Note: Make sure to run mcp_server_clean.py before using this app

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OR Problem Solver UI</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        label {
            font-weight: bold;
            color: #34495e;
            display: block;
            margin-bottom: 10px;
        }
        textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            font-size: 14px;
            font-family: monospace;
            resize: vertical;
            box-sizing: border-box;
        }
        textarea:focus {
            border-color: #3498db;
            outline: none;
        }
        button {
            background-color: #3498db;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 15px;
        }
        button:hover {
            background-color: #2980b9;
        }
        button:disabled {
            background-color: #bdc3c7;
            cursor: not-allowed;
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            background-color: #ecf0f1;
            border-left: 4px solid #3498db;
            border-radius: 0 5px 5px 0;
        }
        .result h2 {
            color: #2c3e50;
            margin-top: 0;
        }
        pre {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            white-space: pre-wrap;
            font-size: 13px;
            line-height: 1.4;
        }
        .error {
            background-color: #e74c3c;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
        }
        .loading {
            display: none;
            text-align: center;
            margin-top: 15px;
            color: #7f8c8d;
        }
        .example {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            margin-top: 20px;
        }
        .example h3 {
            margin-top: 0;
            color: #495057;
        }
        .example-text {
            font-family: monospace;
            font-size: 12px;
            color: #6c757d;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔬 Operations Research Problem Solver</h1>
        
        <form method="POST" id="problemForm">
            <label for="question">Nhập câu hỏi tối ưu hóa (Enter your optimization problem):</label>
            <textarea name="question" id="question" rows="8" placeholder="Ví dụ: Một công ty sản xuất 2 loại sản phẩm A và B. Lợi nhuận từ A là 3 triệu/đơn vị, từ B là 5 triệu/đơn vị. Giới hạn tài nguyên: máy móc 4 giờ cho A, 2 giờ cho B, tổng cộng 100 giờ. Nguyên liệu: 2kg cho A, 3kg cho B, tổng cộng 90kg. Tìm số lượng sản phẩm để maximize lợi nhuận.">{{ question }}</textarea>
            
            <button type="submit" id="submitBtn">🚀 Giải quyết bài toán</button>
            <div class="loading" id="loading">
                <p>⏳ Đang xử lý bài toán... Vui lòng đợi</p>
            </div>
        </form>

        {% if error %}
        <div class="error">
            <strong>❌ Lỗi:</strong> {{ error }}
        </div>
        {% endif %}

        {% if answer %}
        <div class="result">
            <h2>📊 Kết quả giải bài toán:</h2>
            <pre>{{ answer }}</pre>
        </div>
        {% endif %}
        
        <div class="example">
            <h3>💡 Ví dụ về bài toán tối ưu hóa:</h3>
            <div class="example-text">
                Một công ty muốn tối ưu hóa sản xuất với 2 sản phẩm A và B:<br>
                - Lợi nhuận: A = 30$/unit, B = 50$/unit<br>
                - Ràng buộc thời gian: A cần 4h, B cần 2h, tổng cộng ≤ 100h<br>
                - Ràng buộc nguyên liệu: A cần 2kg, B cần 3kg, tổng cộng ≤ 90kg<br>
                - Tìm số lượng A và B để tối đa hóa lợi nhuận
            </div>
        </div>
    </div>

    <script>
        // Form submission handling
        document.getElementById('problemForm').addEventListener('submit', function() {
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('submitBtn').textContent = '⏳ Đang xử lý...';
            document.getElementById('loading').style.display = 'block';
        });
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    question = ""
    answer = ""
    error = ""
    
    if request.method == "POST":
        question = request.form.get("question", "").strip()
        if question:
            try:
                # JSON-RPC 2.0 format for FastMCP
                payload = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "get_operation_research_problem_answer",
                        "arguments": {
                            "user_question": question
                        }
                    },
                    "id": 1
                }
                
                response = requests.post(
                    MCP_API_URL,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'result' in result:
                        answer = str(result['result'])
                    else:
                        answer = str(result)
                else:
                    error = f"Server error: {response.status_code}"
                    
            except requests.exceptions.Timeout:
                error = "Timeout: Bài toán quá phức tạp, vui lòng thử lại"
            except requests.exceptions.ConnectionError:
                error = "Không thể kết nối tới MCP server"
            except Exception as e:
                error = f"Lỗi: {str(e)}"
        else:
            error = "Vui lòng nhập câu hỏi tối ưu hóa"
    
    return render_template_string(HTML, question=question, answer=answer, error=error)

if __name__ == "__main__":
    print("🌐 Starting Flask web server...")
    print("📍 Web interface: http://127.0.0.1:5000")
    print("📡 MCP Server URL:", MCP_API_URL)
    print("\n⚠️  Make sure MCP server is running first!")
    
    app.run(host="127.0.0.1", port=5000, debug=True)
