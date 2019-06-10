pipeline {
    agent { dockerfile true }
    stages {
        stage('Check Version') {
            steps {
                sh 'tracker_config --version'
            }
        }
    }
}