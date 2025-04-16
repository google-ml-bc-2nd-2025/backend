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
                dir('backend/backend') {
                    script {
                        docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                    }
                }
            }
        }
        
        stage('Test') {
            steps {
                dir('backend/backend') {
                    sh 'pip install -r requirements.txt'
                    sh 'python -m pytest tests/ || true'
                }
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    // 기존 컨테이너 중지 및 제거
                    sh 'docker stop backend-container || true'
                    sh 'docker rm backend-container || true'
                    
                    // 새 컨테이너 실행
                    sh """
                        docker run -d \
                        -p 8000:8000 \
                        --name backend-container \
                        --env GOOGLE_API_KEY=${GOOGLE_API_KEY} \
                        --env GOOGLE_MODEL=gemini-1.5-pro \
                        --env DEFAULT_SERVICE=google \
                        ${DOCKER_IMAGE}:${DOCKER_TAG}
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