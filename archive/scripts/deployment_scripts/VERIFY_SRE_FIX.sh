#!/bin/bash
# Verify SRE monitoring fix is working

cd ~/stock-bot

echo "=========================================="
echo "VERIFYING SRE MONITORING FIX"
echo "=========================================="
echo ""

echo "1. Testing SRE health endpoint..."
python3 -c "
from sre_monitoring import get_sre_health
health = get_sre_health()

print('Overall Health:', health.get('overall_health'))
print('')

critical = health.get('critical_issues', [])
warnings = health.get('warnings', [])

if critical:
    print('CRITICAL ISSUES:')
    for issue in critical:
        print(f'  ❌ {issue}')
    print('')
else:
    print('✅ No critical issues')
    print('')

if warnings:
    print('WARNINGS:')
    for warning in warnings:
        print(f'  ⚠️  {warning}')
    print('')
else:
    print('✅ No warnings')
    print('')

# Check signal components
signals = health.get('signal_components', {})
print(f'Signal Components Found: {len(signals)}')
print('')

core_signals = ['options_flow', 'dark_pool', 'insider']
computed_signals = ['iv_term_skew', 'smile_slope']

print('CORE Signals (Required):')
for sig in core_signals:
    status = signals.get(sig, {}).get('status', 'unknown')
    if status == 'healthy':
        print(f'  ✅ {sig}: {status}')
    elif status == 'no_data':
        print(f'  ❌ {sig}: {status} (CRITICAL - MISSING)')
    else:
        print(f'  ⚠️  {sig}: {status}')
print('')

print('COMPUTED Signals (Should exist):')
for sig in computed_signals:
    status = signals.get(sig, {}).get('status', 'unknown')
    if status == 'healthy':
        print(f'  ✅ {sig}: {status}')
    elif status == 'no_data':
        print(f'  ⚠️  {sig}: {status} (may be normal)')
    else:
        print(f'  ⚠️  {sig}: {status}')
print('')

print('ENRICHED Signals (Optional):')
enriched_count = 0
optional_count = 0
for name, sig_data in signals.items():
    if name not in core_signals and name not in computed_signals:
        enriched_count += 1
        status = sig_data.get('status', 'unknown')
        if status == 'optional':
            optional_count += 1
        elif status == 'healthy':
            print(f'  ✅ {name}: {status}')
        else:
            # Don't print optional signals that are missing (normal)
            pass

if enriched_count > 0:
    print(f'  ({enriched_count} enriched signals checked, {optional_count} marked as optional)')
    print('  ✅ Enriched signals are optional - no warnings for missing ones')
print('')

print('==========================================')
if health.get('overall_health') == 'healthy':
    print('✅ SUCCESS: System is HEALTHY')
elif health.get('overall_health') == 'degraded':
    print('⚠️  System is DEGRADED (check warnings above)')
else:
    print('❌ System is CRITICAL (check critical issues above)')
print('==========================================')
"

echo ""
echo "2. Testing dashboard endpoint..."
curl -s http://localhost:5000/api/sre/health | python3 -m json.tool | head -20

echo ""
echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
echo ""
echo "Expected Results:"
echo "  - Overall Health: 'healthy' (if core signals present)"
echo "  - No warnings about enriched signals"
echo "  - Only warnings for missing computed signals (if any)"
echo ""
