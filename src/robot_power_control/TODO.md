> 2026-06-19 現行操作入口：目前手柄鍵位、STAFF/KFS mode、D-pad 視角、五路 relay 順序請先看 `/home/robotics/robocon2026_r1/r1_control_ws/CONTROLLER_USAGE.md`。本文若是舊測試/排查紀錄，內容保留作歷史，不代表目前實機鍵位。

# robot_power_control TODO

## v0.1.0 joystick shutdown

- [x] 建立 `robot_power_control` package
- [x] 新增 `joystick_shutdown_node`
- [x] 預設 `X + Y + B + A` 長按 5 秒
- [x] 預設 `dry_run=true`，避免首次測試誤關機
- [x] 新增 `/robot_power_status`
- [x] 實作 joystick input timeout，超時清空長按計時
- [x] 新增無硬體單元測試
- [x] 新增 README.md
- [x] 新增 TODO.md
- [ ] 實機確認 dry-run 觸發
- [ ] 設定 sudoers 後確認 `dry_run=false` 真關機
- [ ] 根據實機手感決定是否調整 `hold_sec`


## 2026-06-19 手柄 shutdown

- [x] 記錄 `X+Y+B+A` 長按 5 秒作為 shutdown combo
- [ ] 正式使用前確認 `dry_run=false` 且 sudoers 權限正確
- [ ] 比賽前做一次實機關機測試，確認不會被 systemd watcher 立即重啟

maintainer: Hero@EdUHK robotics team 2026 | github: herolch07
