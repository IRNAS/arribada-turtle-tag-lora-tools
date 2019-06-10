pipeline {
    agent {
    	dockerfile {
    		additionalBuildArgs '--build-arg CACHEBUST=$(date +%s)'
    	}
    }
    stages {
        stage('Check Version') {
            steps {
                sh 'tracker_config --version'
            }
        }
    }
}