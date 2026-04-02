# MindWise API

MindWise 学生心理健康评估系统的 FastAPI 后端服务。

## 项目简介

MindWise API 为学生心理健康评估提供后端支持，涵盖学生管理、问卷考试、基于指标的评分计算（原始分与标准化分）以及报告生成。

## 技术栈

- **框架**：FastAPI
- **ORM**：SQLAlchemy 2.x
- **数据库**：SQLite（默认），支持通过 `DATABASE_URL` 切换为其他数据库
- **服务器**：Uvicorn
- **配置**：python-dotenv

## 快速启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API 文档地址：`http://localhost:8000/docs`

## 环境变量

在项目根目录创建 `.env` 文件：

```env
DATABASE_URL=sqlite:///./mindwise.db          # 默认值，可替换为 PostgreSQL 等
SECRET_KEY=your-secret-key-change-in-prod     # JWT 签名密钥，生产环境必须修改
ACCESS_TOKEN_EXPIRE_MINUTES=1440              # Token 有效期（分钟），默认 24 小时
QWEN_API_KEY=your-qwen-api-key               # 阿里云百炼 API Key，报告生成功能必填
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  # 默认值
QWEN_MODEL=qwen-plus                          # 默认模型，可替换
```

## API 接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/v1/health` | 健康检查 | 公开 |
| POST | `/api/v1/auth/login` | 手机号密码登录，返回 JWT | 公开 |
| POST | `/api/v1/auth/register` | 教师注册 | 公开 |
| GET | `/api/v1/students/students` | 获取所有学生及班级信息 | 已登录 |
| GET | `/api/v1/students/{id}` | 获取单个学生详情 | 已登录 |
| GET | `/api/v1/classes/` | 获取班级列表 | 已登录 |
| GET | `/api/v1/exams/` | 获取考试列表 | 已登录 |
| POST | `/api/v1/exams/` | 创建考试 | admin+ |
| GET | `/api/v1/answers/` | 获取答卷记录 | 已登录 |
| POST | `/api/v1/answers/submit` | 提交学生答卷 | 已登录 |
| GET | `/api/v1/indicators/` | 获取心理指标列表 | 已登录 |
| POST | `/api/v1/scores/compute` | 计算某次考试的评分 | admin+ |
| GET | `/api/v1/scores/student/{id}` | 获取学生得分 | 已登录 |
| GET | `/api/v1/reports/{student_id}` | 获取/生成 LLM 分析报告 | admin+ |
| GET | `/api/v1/teachers/` | 获取教师列表 | super_admin |
| GET | `/api/v1/surveys/` | 获取问卷配置 | 已登录 |

### POST `/api/v1/scores/compute`

计算某次考试中所有学生在各指标上的原始分与标准化分。

**请求体：**
```json
{
  "exam_id": 1
}
```

**响应：** 每位学生在每个指标上的 `score_raw`（原始分）和 `score_standardized`（Z-score 标准化分）。

## 项目结构

```
mindwise-api/
├── app/
│   ├── main.py               # FastAPI 应用入口
│   ├── api/v1/endpoints/     # 路由处理（health、students、score、reports、surveys）
│   ├── models/               # SQLAlchemy ORM 模型
│   ├── schemas/              # Pydantic 请求/响应模型
│   ├── db/                   # 数据库 session 与 SQL 加载器
│   ├── core/                 # 数据库引擎配置
│   └── sql/                  # 原生 SQL 查询文件
├── tools/
│   ├── initial_db_tool/      # 数据库初始化与种子数据脚本
│   └── question_insertion_tool/ # 批量插入题目工具
├── requirements.txt
└── .env                      # （不提交）环境变量
```

## 数据库初始化

初始化数据库并导入默认数据（指标、题目、答案等）：

```bash
python tools/initial_db_tool/init_db_with_seeding_data.py
```

## 评分逻辑

1. 对每位学生，按指标计算**原始分**（根据指标-题目映射关系，对题目得分取均值）。
2. 在该次考试范围内，计算每个指标原始分的**均值与标准差**。
3. 进行 **Z-score 标准化**：`score_standardized = (score_raw - mean) / std`
4. 将结果幂等写入 `score_student` 表（重新计算同一考试会覆盖旧数据）。
