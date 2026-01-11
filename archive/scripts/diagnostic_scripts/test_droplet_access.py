#!/usr/bin/env python3
"""
Test Droplet Access - Verify SSH connection and basic operations
"""
import subprocess
import sys

def test_ssh_connection():
    """Test basic SSH connection to droplet"""
    print("=" * 60)
    print("Testing Droplet SSH Access")
    print("=" * 60)
    
    tests = [
        ("Connection Test", "ssh alpaca 'echo Connection successful && whoami'"),
        ("Python Version", "ssh alpaca 'python3 --version'"),
        ("Git Version", "ssh alpaca 'git --version'"),
        ("Project Directory", "ssh alpaca 'ls -la /root/trading-bot-B | head -5'"),
        ("Git Status", "ssh alpaca 'cd /root/trading-bot-B && git branch'"),
    ]
    
    results = []
    for name, command in tests:
        print(f"\n[TEST] {name}...")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"  ✅ SUCCESS")
                output = result.stdout.strip().split('\n')
                for line in output[:3]:  # Show first 3 lines
                    if line.strip():
                        print(f"     {line}")
                results.append((name, True, result.stdout))
            else:
                print(f"  ❌ FAILED")
                print(f"     Error: {result.stderr.strip()}")
                results.append((name, False, result.stderr))
        except subprocess.TimeoutExpired:
            print(f"  ❌ TIMEOUT")
            results.append((name, False, "Timeout"))
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results.append((name, False, str(e)))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, _ in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! Droplet access is working.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(test_ssh_connection())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
