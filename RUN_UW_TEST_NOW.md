# Run UW Endpoint Test Now

The test script has been pushed to Git. To test all UW API endpoints on the droplet:

**Run this on the droplet:**
```bash
cd ~/stock-bot && git pull origin main && bash TRIGGER_UW_TEST.sh
```

This will:
1. Pull the test script
2. Test all UW API endpoints
3. Generate a report: `uw_endpoint_test_results.json`
4. Push results back to Git automatically

The test covers:
- Option flow alerts
- Dark pool data
- Greeks and Greek exposure
- Market tide
- Top net impact
- OI changes
- ETF flows
- IV rank

After running, check `uw_endpoint_test_results.json` for detailed results.

