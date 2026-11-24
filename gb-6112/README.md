# 绒星镶坊·珠宝镶嵌工票转版

预检票号对照规则变化，定位同间重名并核验旧票保留和别名换发方案。

## 业务流程

1. 转版审阅
2. 旧票卷宗
3. 目标试写
4. 改号交接

MySQL 真实排序规则分组、目标唯一键试写和别名碰撞重试。

制签组过去用表格不区分工作间地搜索重名，容易漏掉重音等价、覆盖老票索引，也可能让新别名撞到早已使用的票。上游接收工作间旧票台账，下游由镶嵌技师用工票 ID 找原票并领取新标。

13:00 打开 setting-tickets-north-1124.json 对应的冬展卷。13:04 核对北间 N001 与 N002。13:07 设置允许改号 6 张。13:10 执行试写。13:12 核对 2 组必须改号及西间 W001 保留。13:16 确认 N002 改为 R-N002-2。13:20 导出交接单给制签员。

源卷唯一键使用 utf8mb4_0900_bin。目标中工作间仍按二进制排序规则区分，票号切换到 utf8mb4_0900_ai_ci。先在真实 MySQL 用目标规则分组，从每组取登记最早、ID 最小的票保留。对其余票用目标唯一索引实际拒绝原号，按固定候选序列预留可用别名。演练表在同一会话隔离并自动清除，只产出交接证据。

试写只是预演。制签组在「旧票卷宗」按工票编号发布正式新号：发布在一个事务内覆盖整卷原始工票与全部补票，全成或全无；同卷并发发布只留下第一套新号，中断重试沿用同一套确定性编号；发布后不再接收补票。镶嵌技师按工票编号查号时只看到已整卷发布的新号，旧票号与所属工票的对应关系在任何阶段都可查。

## 启动

```sh
cp -n .env.example .env
docker compose config --quiet
docker compose up -d --build --wait
```

打开 <http://localhost:18313>。OpenAPI 在 <http://localhost:19313/docs>，数据库映射到本机 17813。所有暴露端口只绑定回环地址。Compose 启动 frontend、backend、worker、db、redis，各自通过健康探针检查。数据库、Redis 和共享产物目录各有命名卷；任务状态及导出内容以数据库中的证据为准。

首次启动时幂等载入演示数据。手动载入可运行 `docker compose exec -T backend python -m scripts.seed_demo`。常规停止可用 `docker compose down`。验收环境清理才加 `-v`，它会删除本项目的数据卷。

## 角色与交接

演示账号共用口令 `Demo-DbWorkbench-2026`。

| 登录名 | 角色 | 可执行操作 |
|---|---|---|
| operator | 资料操作员 | 登记业务资料、登记准备期补票、设置「本次允许改号张数」、试写、全卷发布新号、按工票或旧票号查号、下载结果 |
| reviewer | 业务复核员 | 查看执行证据与已发布新号、按工票或旧票号查号、签署单次复核、下载交接单 |
| viewer | 只读观察员 | 查看资料、执行结果、已发布新号及审计，按工票或旧票号查号，下载证据 |

选用「setting-tickets-north-1124.json」对应的演示资料，保存一份复演资料，再以默认参数 6 提交。worker 保存结果摘要、业务明细和 SHA-256。试写确认后在「旧票卷宗」全卷发布新号，再在「改号交接」按工票编号查号并下载交接单，复核员登录后签署。

## 开发说明

| 部分 | 实现 |
|---|---|
| 前端 | 原生 HTML、CSS、JavaScript ES Modules、Nginx |
| 后端 | Python 3.11、FastAPI、SQLAlchemy、JWT |
| 数据库 | MySQL 8.0 |
| 后台执行 | Redis 通知、数据库持久任务队列和行锁、Python worker |

从 `backend/src/domain/scenario.py` 修改业务入口和演示口径，运行 `docker compose up -d --build --wait` 查看变更。数据库表结构在 `backend/src/models` 和 `backend/migrations`，输入模型在 `backend/src/schemas`。业务页和请求接口在 `frontend/src/pages`、`frontend/src/api`。资料、执行、复核三个工作流实体各有独立表和 API；场景输入及结果保留在所属资料和批次中。

角色枚举在 `backend/src/constants/roles.py`、`frontend/src/constants/roles.js`，用于服务端访问控制、账号初始化、前端导航与签署。批次状态在 `backend/src/constants/job_state.py`、`frontend/src/constants/states.js`，用于队列、状态 API、状态标记与轮询。登记、提交、完成和签署事件写入审计表。

`COMPOSE_PROJECT_NAME` 设置栈名，`FRONTEND_PORT`、`BACKEND_PORT`、`DB_PORT` 设置端口。通过 `DB_PASSWORD`、`JWT_SECRET`、`DEMO_PASSWORD` 配置本地凭据。设置 `SEED_DEMO=false` 可关闭演示数据载入，此时数据库初始没有演示账号。数据库密码调整后，已有数据卷需在数据库内同步修改用户密码。

## 验收范围

按 MySQL 目标排序规则试写临时表，通过后由制签组全卷发布正式新号并导出交接单。当前界面用 JSON 编辑业务资料与补票，以 JSON 下载证据。验收关注：补票在切换前均可登记并参与同间判重；整卷一次切换，查号看不到半卷新号；同卷并发发布只认一套新号；切换中断重试不改换已发票号；旧票号与所属工票对应关系始终可查。过程和截图保存在批次的 [验收记录](../../test-artifacts/gb-6112/TESTING.md)。

[MIT License](LICENSE)
