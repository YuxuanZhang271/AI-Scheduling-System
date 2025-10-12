export async function loginUser({ email, password /*, remember*/ }) {

  // —— 演示版：email=test@example.com 且 password=123456 则成功 ——后续改成真实接口
  await new Promise((r) => setTimeout(r, 1000));
  if (email === "test@example.com" && password === "123456") {
    return { success: true, token: "mock-token" };
  }
  return { success: false, error: "Incorrect account or password." };
}
