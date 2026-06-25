> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 [`CONTROLLER_USAGE.md`](CONTROLLER_USAGE.md)。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

# AGENTS 架構審查記錄

日期：2026-06-18

用途：記錄目前 ROS2 workspace 對照 `AGENTS.md` 後發現的架構、package、node、測試與文件問題。這份文件是後續修復用的上下文備忘，不改變任何 runtime 行為。

## 總結判斷

目前 workspace 的 runtime 架構「大方向基本合理」，但不能說已經完全滿足 `AGENTS.md` 要求。

比較準確的判斷是：

- 節點之間大多數是透過 topic 解耦，沒有明顯把所有邏輯塞進同一個 node。
- chassis、joystick、pneumatic、KFS、motor position controller 等 package 基本是按功能拆分。
- 目前實際使用的 node 多數有 timeout / watchdog 或安全輸出設計，方向是對的。
- 但 package 文件、測試、入口點、舊 node 殘留、README 同步程度仍不合格。
- 因此：架構不是完全錯，但尚未達到「可長期維護、可整體遷移、文件可信、測試可信」的要求。

## 對照 AGENTS.md 的合規情況

### 1. ROS2 解耦與接口清晰

狀態：部分滿足。

已滿足的部分：

- joystick driver / joystick bridge / chassis local navigation / Damiao driver / pneumatic bridge / Arduino serial node 大多透過 topic 互相連接。
- Motor7 / Motor8 position controller 使用共用控制邏輯，Motor7 透過 subclass 重用 Motor8 controller，這比複製一份幾乎相同的 controller 更合理。
- KFS gripper 與 arm pneumatic command 最終集中到 Arduino serial node，由同一個 node 實際寫 serial，避免多個正常 runtime node 同時搶 Arduino。

仍存在的問題：

- 舊的 `pneumatic_relay_driver_node` 仍保留為 executable。如果誤啟動，它可能與 `kfs_staff_gripper_arduino_node` 同時開同一個 Arduino serial port。
- 多份 markdown 仍描述舊 node / 舊 topic / 舊 pneumatic channel，文件接口不可信。
- 部分 hardware path、CAN bus 分離、USB-CAN 穩定路徑仍未完成，未來雙 CAN 架構還沒有真正落地。

### 2. Node 可復用、可組合、可遷移

狀態：部分滿足。

做得較好的地方：

- 底盤 local navigation node 綁定 omniwheel / mecanum 類底盤模型，這符合「機構綁定但年份無關」。
- pneumatic bridge 綁定氣動機構，Arduino serial node 綁定 relay protocol，分層方向合理。
- Motor7 / Motor8 position controller 透過參數控制 motor id、目標點、速度、軟限位，方向合理。

不滿足或有風險的地方：

- 某些 package metadata 還是 `TODO` description / license，工程語意不清楚。
- 文件裡有 2026 / R1 / final operation guide 類一次性操作說明，這些可以存在於頂層操作文件，但不能取代 package README 的通用設計說明。
- 舊 node executable 殘留使 package 對新隊員不夠清楚：不知道哪個是正式 runtime、哪個是 legacy/debug。

### 3. Package 級開發規範

狀態：部分滿足。

目前 package 分工大致合理：

- `base_omniwheel_r2_700`：底盤與 Damiao CAN motor 控制。
- `joystick_bridge`：手柄資料轉成 robot command / mode command。
- `my_joystick_driver`：底層 joystick event 讀取。
- `my_joystick_msgs`：自定義 joystick message。
- `arduino_pneumatic_driver`：氣動 command bridge / legacy pneumatic node。
- `kfs_staff_gripper`：KFS 與 Arduino relay serial 聚合。
- `keyboard_teleop`：鍵盤遙控。
- `r1_arm_control`：arm 相關控制。

主要問題：

- `my_joystick_msgs` 缺少 `README.md`，違反每個 package 必須同時有 README 和 TODO 的要求。
- `keyboard_teleop` 沒有 test，`colcon test` 會因 pytest 沒收集到測試而失敗。
- `base_omniwheel_r2_700/setup.py` 內仍有指向不存在 module 的 console script。

## 已確認的具體問題列表

### P0：workspace 測試不能全綠

現象：

- 執行全 workspace `colcon test --event-handlers console_direct+` 時不是全通過。

已確認失敗來源：

- `my_joystick_msgs`
  - `package.xml` schema 順序錯誤。
  - `<member_of_group>rosidl_interface_packages</member_of_group>` 放在 `<test_depend>` 前面，schema 不接受。
- `my_joystick_driver`
  - `flake8` / `pep257` 失敗。
  - `joystick_node.py` 有大量 style 問題與 docstring 問題。
- `keyboard_teleop`
  - pytest 沒有收集到任何測試，返回 exit code 5，導致 package 測試失敗。

影響：

- 不能安全地說 workspace 已達到可維護狀態。
- 之後每次改 code 都很難靠 full test 判斷是否破壞東西。

### P0：`base_omniwheel_r2_700/setup.py` 有不存在的 console scripts

問題：

`src/base_omniwheel_r2_700/setup.py` 仍指向不存在的 module，例如：

- `base_omniwheel_r2_700.damiao_test_node`
- `base_omniwheel_r2_700.vesc_node`
- `base_omniwheel_r2_700.vesc_canbus_speed_control_node`

但目前 package 內實際存在的主要 Python 檔案是：

- `DM_CAN.py`
- `damiao_node.py`
- `direct_motor_test.py`
- `local_navigation_node.py`

影響：

- `ros2 run` 可能出現 entry point 找不到 module。
- 新隊員會以為這些 node 仍可使用。
- package 介面不可信。

### P0：文件與實際 runtime 架構不同步

問題：

以下文件仍有舊 node、舊 topic 或舊 pneumatic command 描述：

- `ARCHITECTURE.md`
- `NODE_GRAPH.md`
- `QUICK_START.md`
- `r1 final operation guide 1.0.md`
- 部分 package README 的歷史段落

常見過期內容包括：

- `arm_gripper_controller_node`
- `arm_gripper_joystick_bridge_node`
- `pneumatic_relay_driver_node`
- 舊 2-channel pneumatic command
- 不存在或已改名的 motor8 joystick bridge 描述

目前實際 runtime 更接近：

- `motor7_position_controller_node`
- `motor8_position_controller_node`
- `motor_position_selector_joystick_bridge_node`
- `kfs_staff_gripper_arduino_node`
- `pneumatic_gripper_joystick_bridge_node`
- `kfs_staff_gripper_joystick_bridge_node`

影響：

- 文件不能作為操作依據。
- 之後修復時容易改錯 node。
- 違反 README 必須隨設計演進更新的要求。

### P1：`my_joystick_msgs` 缺少 README.md

問題：

- `src/my_joystick_msgs` 目前有 `TODO.md`，但缺少 `README.md`。

影響：

- 違反 `AGENTS.md` package 文檔規範。
- 自定義 message 的用途、欄位語意、使用者節點、topic 約定沒有 package 級說明。

### P1：package metadata 仍有 TODO

問題：

以下 package 的 `package.xml` 或 `setup.py` 仍有 `TODO` description / license：

- `base_omniwheel_r2_700`
- `my_joystick_driver`
- `my_joystick_msgs`

影響：

- package 邊界與用途沒有被正式描述。
- 不符合可移植、可維護工程 package 的基本要求。

### P1：舊 pneumatic node 仍可能造成 Arduino serial 衝突

問題：

- `pneumatic_relay_driver_node` 仍在 `arduino_pneumatic_driver/setup.py` 中暴露。
- 新 runtime 使用 `kfs_staff_gripper_arduino_node` 聚合 KFS + arm pneumatic + Arduino serial。
- 如果誤同時啟動兩個 serial writer，可能同時寫同一個 Arduino。

影響：

- relay state 可能互相覆蓋。
- Arduino serial port 可能被佔用。
- 氣動安全狀態可能變得不可信。

建議：

- 若保留 legacy node，README 和 TODO 必須明確標記為 legacy/debug only。
- 更保守的做法是移除正式 launch 入口，只保留測試工具或加啟動警告。

### P1：joystick driver 可能發布 stale input

問題：

- `my_joystick_driver/joystick_node.py` 目前定時發布目前 state。
- 如果 device 斷線時產生明確 `OSError`，程式會 reset 狀態。
- 但如果 read loop 卡住、event 不再更新，而 timer 仍持續發布上一次 state，下游會看到「新鮮 topic」，不一定能判斷這是舊輸入。

影響：

- 若最後一次狀態是非零搖桿值，理論上可能被持續發布。
- 下游只靠 topic timeout 不一定能抓到，因為 topic 還在更新。

建議：

- joystick message 增加 input timestamp 或 sequence freshness 概念。
- joystick driver 若超過一定時間沒有收到 input event，應輸出 neutral state 或標記 disconnected。
- README 必須寫清楚 timeout 條件與安全行為。

### P1：雙 USB-CAN / udev 穩定路徑尚未落地

問題：

之前已討論需要：

- `/dev/can_chassis`
- `/dev/can_mechanism`
- `/dev/arduino_pneumatic`
- `/dev/controller_joystick`

並且兩個 Damiao USB-CAN 不能依賴相同 serial number，需要用 USB `ID_PATH` 分辨物理插口。

目前狀態：

- 這部分需求尚未完整實作。
- 現有架構仍主要是單 CAN / 固定 port 假設。

影響：

- 兩個 USB-CAN 同時使用時可能開錯 bus。
- chassis 和 mechanism CAN 若誤指向同一設備，風險很高。
- 重啟或換 USB port 後設備名稱可能變。

### P2：README 歷史內容保留是對的，但需要新增「目前版本」摘要

問題：

- AGENTS 要求 README 修改時不要刪掉舊內容。
- 目前多個 README 保留了舊段落，這符合「不要刪歷史」。
- 但缺少一個非常清楚的「目前正式 runtime 架構」摘要，導致新舊內容混在一起難以判斷。

影響：

- 新隊員可能照舊章節啟動錯 node。
- 之後 debug 時要讀很多段落才能知道現在到底用哪個。

建議：

- 每個相關 README 最上方新增 `## 目前正式版本`。
- 舊內容保留在 `## 歷史版本 / Legacy 設計記錄` 下。

### P2：controller mapping 文件需要保持和 source code 同步

目前已知重要 mapping：

- D-pad：operator-frame 底盤方向選擇。
- 左搖桿：以操作者視角控制 chassis 平移。
- 右搖桿：底盤旋轉。
- START：切換 Motor7 / Motor8。
- X：目前選中 motor 的三點位置循環。
- L2 / R2：目前選中 motor 的位置微調。
- A / B：目前選中 arm 的 height / gripper toggle。
- SELECT：目前選中 arm 的 inclination toggle。
- P1 = R3，P2 = L3。
- P1/R3：STAFF mode Motor7 inclination/head relay；P2/L3：STAFF mode Motor8 inclination/head relay。

風險：

- 手柄韌體模式或 8BitDo profile 改變後，P1/P2 可能不再映射成 L3/R3。
- 文件必須寫清楚這是目前 controller profile 下的結果，不是所有 controller 的通用硬體真值。

## 目前做得合理的地方

這些不算問題，但後續修復時不要破壞：

- Topic 解耦方向基本正確。
- Motor7 / Motor8 position control 共用 controller，避免複製一份幾乎相同的 code。
- KFS + arm pneumatic 最終由單一 Arduino serial node 實際寫入，方向合理。
- 7 relay protocol 目前已更新為：
  - Relay 1 / Pin 22：KFS gripper，1 開，0 關。
  - Relay 2 / Pin 23：Motor7 arm height，1 高，0 低。
  - Relay 3 / Pin 24：Motor7 arm gripper，1 開，0 關。
  - Relay 4 / Pin 25：Motor8 arm inclination，1 高，0 低。
  - Relay 5 / Pin 26：Motor8 arm height，1 低，0 高。
  - Relay 6 / Pin 27：Motor8 arm gripper，1 開，0 關。
  - Relay 7 / Pin 28：Motor7 arm inclination，1 高，0 低。
- 目前安全狀態應保持為：
  - Arduino full safe state：`[0,0,1,0,1,1,0]`
  - Arm bridge safe state：`[0,1,0,1,1,0]`

## 建議修復順序

- [ ] 新增 `src/my_joystick_msgs/README.md`。
- [ ] 修正 `src/my_joystick_msgs/package.xml` 的 schema 順序。
- [ ] 移除或修正 `base_omniwheel_r2_700/setup.py` 中不存在的 console scripts。
- [ ] 修正 `my_joystick_driver` 的 flake8 / pep257 問題。
- [ ] 為 `keyboard_teleop` 增加最小測試，避免 pytest exit code 5。
- [ ] 清理 package metadata 中的 `TODO` description / license。
- [ ] 更新 `ARCHITECTURE.md`，新增目前正式 runtime 架構，不刪舊版內容。
- [ ] 更新 `NODE_GRAPH.md`，讓 node graph 與目前 launch/script 一致。
- [ ] 更新 `QUICK_START.md`，標記目前應使用的啟動方式。
- [ ] 更新 `r1 final operation guide 1.0.md` 或新增目前正式操作章節，避免舊操作誤導。
- [ ] 明確標記 `pneumatic_relay_driver_node` 為 legacy/debug，或從正式入口中移除。
- [ ] 設計並實作雙 USB-CAN / udev 穩定路徑。
- [ ] joystick driver 增加 input freshness / stale state 防護。
- [ ] 全 workspace 執行 `colcon test --event-handlers console_direct+` 並做到全通過。

## 後續修復時的原則

- 不要為了修文件刪掉舊 README 內容；應新增「目前正式版本」與「歷史版本」區塊。
- 不要把比賽流程、戰術或一次性狀態機寫進底層 driver / controller node。
- 若需要新增硬體差異，優先用 parameter / launch / YAML 解決。
- 每次改控制、硬體、serial、CAN、joystick 相關 node，都要同步 README 的 timeout / safety 行為。
- 修復後必須跑 package 級測試；完成全局清理後再跑 full workspace test。

## 2026-06-18 Autostart 更新

已新增 controller-gated autostart 啟動層：

```text
scripts/wait_and_start_robot.sh
systemd/r1-control-autostart.service
```

`r1_start_base_1_0.sh` 新增 `R1_NO_TMUX_ATTACH=1`，讓 systemd watcher 可以背景建立 `r1_control` tmux session 而不 attach。預設 `STOP_ON_CONTROLLER_LOST=0`，手柄中途關掉不 kill 整套 ROS。

此更新改善啟動流程，但不改變 ROS topic、motor control、pneumatic control 或 watchdog 行為。雙 USB-CAN / udev 穩定路徑仍未完成。

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
