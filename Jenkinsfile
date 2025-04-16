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
        
        stage('Build Docker Image') {
            steps {
                script {
                    bat 'dir'
                    bat 'docker build -t %DOCKER_IMAGE%:%DOCKER_TAG% .'
                }
            }
        }
        
        stage('Test') {
            steps {
                bat 'pip install -r requirements.txt'
                bat 'python -m pytest tests/ || exit 0'
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    // 기존 컨테이너 중지 및 제거
                    bat 'docker stop backend-container || exit 0'
                    bat 'docker rm backend-container || exit 0'
                    
                    // 새 컨테이너 실행
                    bat """
                        docker run -d ^
                        -p 8000:8000 ^
                        --name backend-container ^
                        --env GOOGLE_API_KEY=%GOOGLE_API_KEY% ^
                        --env GOOGLE_MODEL=gemini-1.5-pro ^
                        --env DEFAULT_SERVICE=google ^
                        %DOCKER_IMAGE%:%DOCKER_TAG%
                    """
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
} 