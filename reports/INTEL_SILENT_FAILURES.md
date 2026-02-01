# Silent Failure Detection

**Generated:** 2026-01-28T17:19:45.033317+00:00 (UTC)
**Method:** grep/code scan for try/except swallow, default fallbacks, feature flags, TODO/deprecated.

---

- **logic_stagnation_detector.py** (try/except pass|continue): `except:
                pass`
- **logic_stagnation_detector.py** (try/except pass|continue): `except ImportError:
            pass`
- **logic_stagnation_detector.py** (try/except pass|continue): `except Exception:
            pass`
- **logic_stagnation_detector.py** (try/except pass|continue): `except:
                    pass`
- **logic_stagnation_detector.py** (try/except pass|continue): `except:
            pass`
- **comprehensive_service_fix.py** (try/except pass|continue): `except:
                pass`
- **fix_weights_and_check_trading.py** (try/except pass|continue): `except:
                continue`
- **fix_weights_and_check_trading.py** (.get(..., {})): `.get("cluster", {})`
- **state_manager.py** (.get(..., {})): `.get('open_positions', {})`
- **state_manager.py** (.get(..., {})): `.get("open_positions", {})`
- **state_manager.py** (.get(..., {})): `.get(symbol, {})`
- **investigate_score_stagnation_on_droplet.py** (try/except pass|continue): `except:
                continue`
- **investigate_score_stagnation_on_droplet.py** (.get(..., {})): `.get(symbol, {})`
- **investigate_score_stagnation_on_droplet.py** (.get(..., {})): `.get('components', {})`
- **fetch_droplet_data_and_generate_report.py** (try/except pass|continue): `except:
                                pass`
- **fetch_droplet_data_and_generate_report.py** (try/except pass|continue): `except:
                                    pass`
- **fetch_droplet_data_and_generate_report.py** (.get(..., {})): `.get("context", {})`
- **full_pipeline_verification.py** (try/except pass|continue): `except:
            pass`
- **full_pipeline_verification.py** (.get(..., {})): `.get("components", {})`
- **run_droplet_trading_audit.py** (try/except pass|continue): `except:
                    pass`
- **run_droplet_trading_audit.py** (try/except pass|continue): `except:
            pass`
- **run_droplet_trading_audit.py** (try/except pass|continue): `except:
                        pass`
- **run_droplet_trading_audit.py** (.get(..., {})): `.get("_metadata", {})`
- **comprehensive_score_diagnostic.py** (try/except pass|continue): `except:
                    pass`
- **comprehensive_score_diagnostic.py** (.get(..., {})): `.get(symbol, {})`
- **comprehensive_score_diagnostic.py** (.get(..., {})): `.get('components', {})`
- **comprehensive_no_trades_diagnosis.py** (try/except pass|continue): `except:
                        pass`
- **comprehensive_no_trades_diagnosis.py** (try/except pass|continue): `except:
        pass`
- **comprehensive_no_trades_diagnosis.py** (.get(..., {})): `.get(t, {})`
- **comprehensive_no_trades_diagnosis.py** (.get(..., {})): `.get("block_reasons", {})`
- **inspect_droplet_uw_cache_fields.py** (.get(..., {})): `.get(t, {})`
- **failure_point_monitor.py** (try/except pass|continue): `except:
                        pass`
- **failure_point_monitor.py** (.get(..., {})): `.get("statuses", {})`
- **failure_point_monitor.py** (.get(..., {})): `.get("weight_bands", {})`
- **counter_intelligence_analysis.py** (try/except pass|continue): `except:
        pass`
- **counter_intelligence_analysis.py** (try/except pass|continue): `except:
                continue`
- **counter_intelligence_analysis.py** (.get(..., {})): `.get("context", {})`
- **counter_intelligence_analysis.py** (.get(..., {})): `.get("components", {})`
- **health_supervisor.py** (try/except pass|continue): `except:
                    pass`
- **health_supervisor.py** (try/except pass|continue): `except Exception:
            pass`
- **health_supervisor.py** (try/except pass|continue): `except Exception as e:
                pass`
- **complete_workflow_fix.py** (.get(..., {})): `.get(sym, {})`
- **shadow_analysis_blocked_trades.py** (try/except pass|continue): `except:
        pass`
- **shadow_analysis_blocked_trades.py** (try/except pass|continue): `except:
                    continue`
- **shadow_analysis_blocked_trades.py** (.get(..., {})): `.get("components", {})`
- **debug_score_calculation.py** (try/except pass|continue): `except:
            continue`
- **debug_score_calculation.py** (.get(..., {})): `.get('components', {})`
- **monitoring_guards.py** (try/except pass|continue): `except:
                    pass`
- **monitoring_guards.py** (try/except pass|continue): `except:
            pass`
- **monitoring_guards.py** (.get(..., {})): `.get("context", {})`
- **architecture_self_healing.py** (TODO/FIXME/deprecated): `deprecated`
- **score_validation.py** (try/except pass|continue): `except:
            pass`
- **adaptive_signal_optimizer.py** (try/except pass|continue): `except Exception:
            pass`
- **adaptive_signal_optimizer.py** (.get(..., {})): `.get(component, {})`
- **adaptive_signal_optimizer.py** (.get(..., {})): `.get("regime_performance", {})`
- **adaptive_signal_optimizer.py** (.get(..., {})): `.get("sector_performance", {})`
- **comprehensive_diagnostic.py** (try/except pass|continue): `except:
                pass`
- **comprehensive_learning_scheduler.py** (try/except pass|continue): `except:
            pass`
- **comprehensive_learning_scheduler.py** (try/except pass|continue): `except:
        pass`
- **comprehensive_learning_scheduler.py** (.get(..., {})): `.get("learning_results", {})`
- **comprehensive_learning_scheduler.py** (.get(..., {})): `.get("trends", {})`
- **comprehensive_learning_scheduler.py** (.get(..., {})): `.get("regime_analysis", {})`
- **comprehensive_learning_scheduler.py** (.get(..., {})): `.get("monthly", {})`
- **comprehensive_learning_scheduler.py** (.get(..., {})): `.get("long_term_analysis", {})`