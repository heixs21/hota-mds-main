### 镗床与机器人 OPC UA 数据采集接口定义 v1.0

#### 1. 连接配置

| 设备类型    | 设备编号    | 端点 URL                                                                                                                                                                                                                                                                                     | 认证方式   | 用户名           | 密码         |
| :------ | :------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----- | :------------ | :--------- |
| **镗床**  | 1 - 8   | `opc.tcp://192.168.32.81:4840` <br> `opc.tcp://192.168.32.21:4840` <br> `opc.tcp://192.168.32.31:4840` <br> `opc.tcp://192.168.32.41:4840` <br> `opc.tcp://192.168.32.51:4840` <br> `opc.tcp://192.168.32.61:4840` <br> `opc.tcp://192.168.32.71:4840` <br> `opc.tcp://192.168.32.11:4840` | 用户名/密码 | `OpcUaClient` | `DWIN1234` |
| **机器人** | 线 1 - 8 | `opc.tcp://192.168.32.4:4840` <br> `opc.tcp://192.168.32.14:4840` <br> `opc.tcp://192.168.32.24:4840` <br> `opc.tcp://192.168.32.34:4840` <br> `opc.tcp://192.168.32.44:4840` <br> `opc.tcp://192.168.32.54:4840` <br> `opc.tcp://192.168.32.64:4840` <br> `opc.tcp://192.168.32.74:4840`  | 匿名 / 无 | -             | -          |

#### 2. 命名空间与索引说明

- **命名空间 NS2**：用于所有 CNC 系统变量（镗床）。
- **命名空间 NS4**：用于机器人状态变量。
- **索引参数说明**：
    - `<Area index>`：通常指 **通道号**（对于单通道系统，固定为 1）。
    - `<Row index>`：指 **轴号**、**主轴号**、**TOA 号** 或 **报警列表索引**。
    - `u[...]` 语法：表示数组下标，例如 `u[1, 1]` 表示通道 1 的第 1 个元素。

#### 3. 镗床 CNC 数据点详细定义 (NS2)

| 中文描述         | 变量标识符                | 完整 Node ID 路径 (Browse Path)                                                                       | 数据类型   | 备注 / 值映射                     |
| :----------- | :------------------- | :------------------------------------------------------------------------------------------------ | :----- | :--------------------------- |
| **CNC 基本信息** |                      |                                                                                                   |        |                              |
| CNC 型号       | `CncVersion`         | `/Nck/Configuration/nckVersion`                                                                   | Double |                              |
| CNC 类型       | `CncType`            | `/Nck/Configuration/nckType`                                                                      | UInt16 |                              |
| 序列号 (CF卡)    | `CncSerialNo`        | `/Nck/State/hwProductSerialNr[1]`                                                                 | String | 长度 16                        |
| 最大轴数         | `CncMaxAxisNum`      | `/Nck/Configuration/maxnumGlobMachAxes`                                                           | UInt16 |                              |
| 有效轴数         | `CncValidAxisNum`    | `/Nck/Configuration/numGlobMachAxes`                                                              | UInt16 |                              |
| 主轴数          | `CncSpindleNum`      | `/Channel/Configuration/numSpindles[u<Area>, <Row>]`                                              | UInt16 | `<Area>`: 通道号                |
| 主轴最高转速       | `CncSpindleMaxSpeed` | `/Channel/LogicalSpindle/acSmaxVelo[u<Area>, <Row>]`                                              | Double | `<Area>`: 通道号, `<Row>`: 主轴号  |
| **运行状态**     |                      |                                                                                                   |        |                              |
| CNC 状态       | `CncState`           | `/Channel/State/progStatus[u<Area>]`                                                              | UInt16 | 1=中断, 2=停止, 3=运行, 4=等待, 5=中止 |
| 急停状态         | `CncEmg`             | 未提供具体路径                                                                                           | Int    |                              |
| 工作模式         | `CncWorkModel`       | `/Bag/State/opMode[u<Area>]`                                                                      | UInt16 | 0=JOG手动, 1=MDI, 2=AUTO自动     |
| 轴移动状态        | `CncAxisMoveState`   | `/Nck/MachineAxis/status[<Row>]`                                                                  | UInt16 | 0=正向移动, 1=负向移动, 2=粗到位, 3=精到位 |
| **程序信息**     |                      |                                                                                                   |        |                              |
| 主程序号         | `MainProgNo`         | `/Channel/ProgramInfo/selectedWorkPProg[u<Area>, <Row>]`                                          | String | 长度 160                       |
| 子程序号         | `SubProgNo`          | `/Channel/ProgramInfo/progName[u<Area>]`                                                          | String | 长度 32                        |
| 执行行号         | `ExeLine`            | `/Channel/ProgramInfo/blockNoStr[u<Area>]` 或 `/Channel/ProgramInfo/actLineNumber[u<Area>, <Row>]` | String | 长度 12                        |
| 执行代码         | `ExeProgCode`        | `/Channel/ProgramInfo/actBlock[u<Area>, <Row>]`                                                   | String | 长度 66, `<Row>`=1             |
| **计时器**      |                      |                                                                                                   |        |                              |
| 切削时间         | `CycTime`            | `/Channel/ChannelDiagnose/cycleTime[u<Area>, <Row>]`                                              | Int64  | `<Row>`=1                    |
| 程序加工时间       | `OperationTime`      | `/Channel/ChannelDiagnose/operatingTime[u<Area>, <Row>]`                                          | Int64  | `<Row>`=1                    |
| 系统累计开机时间     | `CncSumBootTime`     | `/Nck/ChannelDiagnose/setupTime[<Row>]`                                                           | Int64  | `<Row>`=1                    |
| **速度与倍率**    |                      |                                                                                                   |        |                              |
| 切削倍率         | `CutRate`            | `/Channel/GeometricAxis/feedRateOvr[u<Area>, <Row>]`                                              | Double | `<Area>`: 通道号, `<Row>`: 轴号   |
| 主轴倍率         | `SpRate`             | `/Channel/Spindle/speedOvr[u<Area>, <Row>]`                                                       | Double | `<Area>`: 通道号, `<Row>`: 主轴号  |
| 切削指定速度 F     | `CutOrderSpeed`      | `/Channel/GeometricAxis/cmdFeedRate[u<Area>, <Row>]`                                              | Double | `<Area>`: 通道号, `<Row>`: 轴号   |
| 切削实际速度       | `CutActSpeed`        | `/Channel/GeometricAxis/actFeedRate[u<Area>, <Row>]`                                              | Double | `<Area>`: 通道号, `<Row>`: 轴号   |
| 主轴指定速度 S     | `SpOrderSpeed`       | `/Channel/Spindle/cmdSpeed[u<Area>, <Row>]`                                                       | Double | `<Area>`: 通道号, `<Row>`: 主轴号  |
| 主轴实际速度       | `SpActSpeed`         | `/Channel/Spindle/actSpeed[u<Area>, <Row>]`                                                       | Double | `<Area>`: 通道号, `<Row>`: 主轴号  |
| **坐标数据**     |                      |                                                                                                   |        |                              |
| 轴名称          | `AxisName`           | `/Channel/Drive/AXCONF_CHANAX_NAME_TAB[<Row>]`                                                    | String | `<Row>`: 轴号                  |
| 机械坐标         | `MachineCoor`        | `/Channel/MachineAxis/actToolBasePos[u<Area>, <Row>]`                                             | Double | `<Area>`: 通道号, `<Row>`: 轴号   |
| 绝对编程坐标       | `AbsoluteCoor`       | `/Channel/GeometricAxis/actToolBasePos[u<Area>, <Row>]`                                           | Double | `<Area>`: 通道号, `<Row>`: 轴号   |
| **报警信息**     |                      |                                                                                                   |        |                              |
| 报警数量         | `alarmNums`          | `/Nck/State/numAlarms`                                                                            | UInt16 |                              |
| 报警类型         | `AlarmType`          | `/Nck/SequencedAlarms/clearInfo[<Row>]`                                                           | Int64  | `<Row>`: 报警索引号               |
| 报警号          | `AlarmNo`            | `/Nck/SequencedAlarms/textIndex[<Row>]`                                                           | Int64  | `<Row>`: 报警索引号               |

#### 4. 机器人数据点详细定义 (NS4)

| 中文描述 | 变量标识符                   | Node ID (建议格式) | 数据类型    | 备注  |         |           |
| :--- | :---------------------- | :------------- | :------ | :-- | ------- | --------- |
| 运行状态 | `Robot_Run`             | `NS4           | Numeric | 2`  | Numeric | 状态值       |
| 停止状态 | `Robot_Stop`            | `NS4           | Numeric | 3`  | Numeric | 状态值       |
| 故障状态 | `Robot_Fault`           | `NS4           | Numeric | 4`  | Numeric | 状态值       |
| 物料编码 | `Robot_MaterialCode`    | `NS4           | Numeric | 5`  | Numeric | 当前加工物料代码  |
| 生产数量 | `Robot_ProductionCount` | `NS4           | Numeric | 6`  | Numeric | 累计/当前生产数量 |
