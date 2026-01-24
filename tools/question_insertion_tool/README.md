# 心理测评题目处理工具包

本工具包包含两个脚本，用于：
1. **`parse_questions.py`**：将 Word 文档转换为结构化 JSON  
2. **`import_questions.py`**：将 JSON 导入数据库  

> ⚠️ **重要前提**：Word 文档必须**预先删除量表标题**（如“一、Derryberry与Reed(2002)《注意控制量表》”、“二、张业恒（2007）《中学生学习策略量表》”），否则会被误认为题目。

---

## 第一步：从 Word 生成 JSON（`parse_questions.py`）

### 🛠️ 使用前准备
1. **手动清理 Word 文档**：
   - 删除所有量表标题（如 `一、Derryberry与Reed(2002)《注意控制量表》`、`二、张业恒（2007）《中学生学习策略量表》`）
   - 保留纯题目和选项，格式示例：
   ```
    x.[题干文本]
    A、[选项] B、[选项] C、[选项] D、[选项] ...
    ```

2. 将清理后的 `.docx` 文件放入 `tools/question_insertion_tool` 文件夹

### ▶️ 运行步骤
1. 安装依赖：
   ```bash
   pip install python-docx
   ```
2. （可选）修改 parse_questions.py 中的文件名：
    ```python
    INPUT_DOCX = "./test1.docx" 
    OUTPUT_JSON = "./questions.json"
    ```
3. 运行脚本并选择模式：
    ```bash
    python parse_questions.py
    ```
    - **模式1:** 生成后手动修改 `is_negative`
    - **模式2：** 运行时输入反向题号（如 `3,7,12-15`）
      - 本模式下需输入题目总题号，例如二号表中的第3题如为反向记分题目，需输入23（20+3）为题号，因为一号表中共有20道题
      - 【临时】初始测试题组可用：`1-3, 6-8, 11, 12, 15, 16, 20, 22, 26, 38, 42, 56, 58, 60, 68, 76, 81-83, 88-90`
4. 输出文件：`questions.json`

## 第二步：将 JSON 导入数据库（`import_questions.py`）
### ▶️ 运行步骤
1. 根据需求修改
    ```python
    DATABASE_URL = "sqlite:///../../mindwise.db" # 设为mindwise.db实际位置
    ...
    CLEAR_EXISTING = False  # 设为 True 会删除所有旧题目！仅首次导入或测试数据时建议开启
    ```
2. 运行导入脚本
    ```bash
    python import_questions.py
    ```