// server.js
const express = require("express");
const mysql = require("mysql2/promise"); // Promise 기반 API 사용
const app = express();
const port = 8000;

// JSON 요청 파싱을 위한 미들웨어
app.use(express.json());

// MySQL 연결 풀 생성 (환경에 맞게 수정)
const pool = mysql.createPool({
  host: "localhost",
  user: "your_mysql_user",       // MySQL 사용자명
  password: "your_mysql_password", // MySQL 비밀번호
  database: "your_database_name",  // 사용하고자 하는 데이터베이스 이름
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
});

// 회원가입 API 엔드포인트 (/register)
app.post("/register", async (req, res) => {
  try {
    // 프론트엔드에서 전송한 데이터 받기
    const { username, email, password, contact } = req.body;
    
    // 필수 값 검증
    if (!username || !email || !password || !contact || !contact.type || !contact.value) {
      return res.status(400).json({ detail: "필수 정보가 누락되었습니다." });
    }

    // INSERT SQL 쿼리 준비
    const sql = `
      INSERT INTO users (username, email, password, contact_type, contact_value)
      VALUES (?, ?, ?, ?, ?)
    `;
    const values = [username, email, password, contact.type, contact.value];

    // 쿼리 실행
    const [result] = await pool.execute(sql, values);

    // 결과 반환 (예: 삽입된 행의 ID)
    res.status(201).json({ message: "회원가입 성공", user_id: result.insertId });
  } catch (err) {
    console.error("회원가입 오류:", err);
    res.status(500).json({ detail: "서버 오류로 회원가입에 실패했습니다." });
  }
});

// 서버 실행
app.listen(port, () => {
  console.log(`서버가 http://localhost:${port} 에서 실행 중입니다.`);
});
