pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'backend-app'
        DOCKER_TAG = 'latest'
        GOOGLE_API_KEY = credentials('google-api-key')
        GOOGLE_MODEL = 'gemini-1.5-pro'
        DEFAULT_SERVICE = 'google'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build and Deploy') {
            steps {
                script {
                    // 기존 컨테이너 중지 및 제거
                    bat 'docker-compose down || exit 0'
                    
                    // Docker Compose로 빌드 및 실행
                    bat 'docker-compose up -d --build'
                }
            }
        }
        
        stage('Test') {
            steps {
                script {
                    // 서비스가 완전히 시작될 때까지 대기
                    bat 'timeout /t 10'
                    
                    // 헬스 체크
                    bat 'curl http://localhost:8000/'
                }
            }
        }
    }
    
    post {
        failure {
            script {
                bat 'docker-compose down'
            }
        }
        always {
            cleanWs()
        }
    }
} 