**Title:** Remove non-functional Forgot Password / OTP flow

**Description:**
The Forgot Password page looked like a working OTP-based password reset, but on inspection it had no real logic behind it:
- "Send OTP" didn't call any API — it just showed a fake message that revealed the OTP itself ("Demo: Use OTP 123456")
- There was no input field to even enter the OTP
- "Reset Password" didn't verify the OTP or persist any password change — it just showed a fake success message

Since it was misleading rather than actually functional, removed it entirely:
- Deleted `ForgotPasswordView.vue`
- Removed the `/forgot-password` route
- Removed the "Forgot Password?" link from the Login page
- Removed the unused `/auth/forgot-password` mock handler

**Type:** Chore / Cleanup
**Status:** Done
