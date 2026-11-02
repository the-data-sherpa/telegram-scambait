"""Quick sanity checks for the detector. Run: python test_detector.py"""
from detector import score_message

SPAM = [
    "Hello dear, I came across your profile. I want to share a crypto investment with huge ROI",
    "Congratulations! You are a winner. Claim your prize now at http://x.co/win",
    "Hi dear",
    "Earn $5000 from home, message me on whatsapp",
    "Double your bitcoin, send to this wallet address and get 200% returns",
]

HAM = [
    "Hey, are we still on for lunch tomorrow?",
    "Can you send me that report when you get a sec?",
    "Thanks for the help earlier, really appreciate it!",
    "Mum said to call her tonight",
    "Did you watch the game last night?",
]


def main():
    ok = True
    print("SPAM (want is_spam=True):")
    for t in SPAM:
        s = score_message(t)
        flag = "✅" if s.is_spam else "❌"
        if not s.is_spam:
            ok = False
        print(f"  {flag} {s.points}pts {s.reasons} :: {t[:50]}")

    print("\nHAM (want is_spam=False):")
    for t in HAM:
        s = score_message(t)
        flag = "✅" if not s.is_spam else "❌ FALSE POSITIVE"
        if s.is_spam:
            ok = False
        print(f"  {flag} {s.points}pts {s.reasons} :: {t[:50]}")

    print("\nRESULT:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
