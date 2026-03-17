// Vercel serverless: trả về URL backend để frontend gọi API
// Cấu hình biến môi trường LEGAL_AI_API_URL trong Vercel Dashboard
module.exports = (req, res) => {
  const apiUrl = process.env.LEGAL_AI_API_URL || '';
  res.setHeader('Content-Type', 'application/javascript');
  res.setHeader('Cache-Control', 'public, max-age=60');
  res.end(`window.__LEGAL_AI_API__="${apiUrl.replace(/"/g, '\\"')}";`);
};
