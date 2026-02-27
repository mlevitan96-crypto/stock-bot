# 04 Data freshness

## System date / timezone
```
Wed Feb 18 19:49:26 UTC 2026
UTC
```

## data/ and state/ (ls -la)
```
-rw-r--r-- 1 root root    8878 Feb 18 03:29 data/dashboard_panel_inventory.json
-rw-r--r-- 1 root root 2155755 Jan 31 01:24 data/uw_expanded_intel.json
-rw-r--r-- 1 root root 6838416 Feb 18 19:49 data/uw_flow_cache.json
-rw-r--r-- 1 root root  126205 Jan 27 15:18 data/uw_flow_cache.json.corrupted.1769527139.json
-rw-r--r-- 1 root root 2251530 Jan 28 18:34 data/uw_flow_cache.json.corrupted.1769625275.json
-rw-r--r-- 1 root root 5395601 Jan 28 18:37 data/uw_flow_cache.json.corrupted.1769625465.json
-rw-r--r-- 1 root root 2518317 Jan 30 15:54 data/uw_flow_cache.json.corrupted.1769788440.json
-rw-r--r-- 1 root root 6829660 Feb  3 17:34 data/uw_flow_cache.json.corrupted.1770140078.json
-rw-r--r-- 1 root root 6780983 Feb  5 14:30 data/uw_flow_cache.json.corrupted.1770301845.json
-rw-r--r-- 1 root root 6969933 Feb  9 04:23 data/uw_flow_cache.json.corrupted.1770611015.json
-rw-r--r-- 1 root root 2706264 Feb  9 19:53 data/uw_flow_cache.json.corrupted.1770666813.json
-rw-r--r-- 1 root root  126230 Feb 10 15:11 data/uw_flow_cache.json.corrupted.1770736273.json
-rw-r--r-- 1 root root 1419358 Feb 11 19:42 data/uw_flow_cache.json.corrupted.1770838951.json
-rw-r--r-- 1 root root 6824404 Feb 12 15:48 data/uw_flow_cache.json.corrupted.1770911326.json
-rw-r--r-- 1 root root 2272647 Feb 13 19:16 data/uw_flow_cache.json.corrupted.1771010189.json
-rw-r--r-- 1 root root 1765965 Feb 13 19:27 data/uw_flow_cache.json.corrupted.1771010865.json
-rw-r--r-- 1 root root 6836943 Feb 14 11:50 data/uw_flow_cache.json.corrupted.1771069815.json
-rw-r--r-- 1 root root 6579201 Feb 17 15:55 data/uw_flow_cache.json.corrupted.1771343749.json
-rw-r--r-- 1 root root 3427338 Feb 17 16:46 data/uw_flow_cache.json.corrupted.1771346805.json
-rw-r--r-- 1 root root 3302073 Feb 17 16:46 data/uw_flow_cache.json.corrupted.1771346807.json
-rw-r--r-- 1 root root      168 Feb 18 19:49 state/alpaca_positions.json
-rw-r--r-- 1 root root      121 Dec 22 18:42 state/bayes_profiles.json
-rw-r--r-- 1 root root      180 Feb 18 19:49 state/bot_heartbeat.json
-rw-r--r-- 1 root root 18484641 Feb 18 00:27 state/causal_analysis_state.json
-rw-r--r-- 1 root root      130 Dec 13 20:59 state/champions.json
-rw-r--r-- 1 root root    23756 Dec 21 00:09 state/comprehensive_learning_state.json
-rw-r--r-- 1 root root     3096 Jan 31 01:24 state/core_universe.json
-rw-r--r-- 1 root root      185 Feb 17 21:48 state/correlation_snapshot.json
-rw-r--r-- 1 root root   131994 Dec 21 00:09 state/counterfactual_state.json
-rw-r--r-- 1 root root     1970 Feb 17 21:20 state/cron_health_failures.json
```

## Files modified in last 60 min
```
./profiles.json
./data/uw_flow_cache.json
./state/market_context_v2.json
./state/uw_usage_state.json
./state/internal_positions.json
./state/bot_heartbeat.json
./state/executor_state.json
./state/logic_stagnation_state.json
./state/regime_posture_state.json
./state/position_metadata.json
./state/sector_tide_state.json
./state/health.json
./state/alpaca_positions.json
./state/smart_poller.json
./state/signal_funnel_state.json
./state/fail_counter.json
./state/last_scores.json
./state/live_paper_run_state.json
./state/regime_detector_state.json
./state/uw_cache/f5c54d7947f053bcd45dde309a6419f16f5369edf30c5f4c693fb7a80f096153.json
./state/uw_cache/c29a8fe23c05200254ee56a2fb0a2e38f95f1dc71df784a53097d673e08a99be.json
./state/uw_cache/3600dee79f348cf9cf0566b5e9db6fe5465e2950756a755dae5ef9518500258d.json
./state/uw_cache/2a8b302ddf30b896cbf13fb390acfae47e4bba6e183436c854bf12317f277b2f.json
./state/uw_cache/e5d0cb72407b119206d756a6c8a2093bc3632729cf439a221ca885cc9d2697ab.json
./state/uw_cache/decb7d7a4345da3e4d85b8ba7227edf1c0d176f674588c2077d2951572ec2a68.json
./state/uw_cache/9de2e9a3f48e474aa3756887df9d6845df9f80c3e596b7c1fa68eb0ed55184ac.json
./state/uw_cache/e98821d16a56154540cf18ef8dc152e302f08c44d3fe52be545b0d2a7adb9851.json
./state/uw_cache/53d2201bb14ec53cf423894dfa91add0c21ae630be496473a90c6330d19d476a.json
./state/uw_cache/e59ebdf5fa0a7f7d782889bbbe44e3fd3eb4ca92d73314bad05146fca9f7a0cf.json
./state/uw_cache/aa707376a5e6adc8c0b91be0c69bf716e8dd02740a151c316859fe94c9d8dbdd.json
```