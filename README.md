# PRIVACY-PRESERVING BIOMETRIC AUTHENTICATION SYSTEM

A secure biometric authentication platform built using Flask, OpenCV, Face Recognition, MySQL, and Hybrid Homomorphic Encryption. The system enables webcam-based facial authentication while preserving user privacy by encrypting biometric templates before storage and verification.

## PROJECT STRUCTURE

```
.
├── app.py                     # Main Flask application
├── database.py                # Database connection setup
├── requirements.txt           # Project dependencies
├── .env                       # Environment variables
├── biometric.db / MySQL       # Database
│
├── static
│   ├── css
│   ├── js
│   └── images
│
├── templates
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   └── result.html
│
├── face_recognition_module.py # Face detection and embedding extraction
├── encryption_module.py       # Hybrid Homomorphic Encryption logic
├── webcam_module.py           # Webcam capture functionality
└── README.md
```

## FEATURES

* Webcam-based face registration
* Secure facial authentication
* Hybrid Homomorphic Encryption
* Encrypted biometric template storage
* User registration and login
* Real-time identity verification
* Privacy-preserving biometric matching
* Database integration
* Secure session management

## SECURITY FEATURES

### Hybrid Homomorphic Encryption

Biometric embeddings are encrypted before storage and matching, preventing exposure of sensitive biometric data.

### Secure Authentication

User identities are verified without decrypting stored biometric templates.

### Password Hashing

Passwords are hashed using industry-standard cryptographic techniques.

### Session Management

Secure user sessions prevent unauthorized access.

### Environment Variables

Sensitive credentials and secret keys are stored securely in a `.env` file.

### Database Security

Parameterized queries are used to mitigate SQL injection attacks.

## ENVIRONMENT VARIABLES (.env)

Create a `.env` file in the project root:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=biometric_authentication

SECRET_KEY=your_secret_key
```

## TECHNOLOGIES USED

### Frontend

* HTML
* CSS
* JavaScript

### Backend

* Python
* Flask

### Database

* MySQL

### Libraries

* OpenCV
* face_recognition
* NumPy
* Cryptography
* TenSEAL (for Homomorphic Encryption)

## SYSTEM WORKFLOW

1. User registers using webcam.
2. Facial image is captured.
3. Face embeddings are generated.
4. Embeddings are encrypted using Hybrid Homomorphic Encryption.
5. Encrypted templates are stored in the database.
6. During login, a new facial image is captured.
7. Encrypted matching is performed.
8. Authentication result is returned without revealing biometric data.

## INSTALLATION

### Clone Repository

```bash
git clone https://github.com/your-username/Privacy-Preserving-Biometric-Authentication-System.git

cd Privacy-Preserving-Biometric-Authentication-System
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Database

Create a MySQL database:

```sql
CREATE DATABASE biometric_authentication;
```

### Run the Application

```bash
python app.py
```

Open in browser:

```
http://127.0.0.1:5000
```

## FUTURE ENHANCEMENTS

* Multi-factor authentication
* Liveness detection
* Cloud deployment
* Mobile application support
* Deep learning-based face recognition
* Blockchain-based audit logging

## AUTHOR

Radhika P A

## LICENSE

This project is developed for educational, research, and academic purposes.
