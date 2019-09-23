#!/usr/bin/env groovy
import groovy.transform.Field


@Field def SHUB_APIKEY_CREDENTIAL_ID = 'scrapinghub-hardcore-apikey'

@Field def STATUS_SUCCESS = 'Success'
@Field def STATUS_FAILURE = 'Failure'

@Field def COLOR_OK = '#36A64F'
@Field def COLOR_ERROR = '#D00000'
@Field def COLOR_WARNING = '#DAA038'


pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: scm.branches,
                    extensions: scm.extensions + [[$class: 'LocalBranch']],
                ])
                script {
                    env.git_commit_short = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
                }
            }
        }
        stage('Test') {
            when { expression { env.BRANCH_NAME in ['develop', 'stage', 'master'] } }
            steps {
                runTest()
            }
            post {
                always {
                    junit 'test_result/test_report.xml'
                    cobertura coberturaReportFile: 'test_result/coverage.xml'
                }
                success {
                    onSuccess('Test')
                }
                failure {
                    onFail('Test')
                }
            }
        }
        stage('Deploy') {
            when { expression { env.BRANCH_NAME in ['stage', 'master'] } }
            steps {
                setupDeployEnv()
                runDeploy()
            }
            post {
                success {
                    onSuccess('Deploy')
                }
                failure {
                    onFail('Deploy')
                }
            }
        }
    }
}


//////////////////////////////////////////////////////////////////////////////////////////////


def runTest() {
    sh 'docker-compose -f docker-compose.test.yml up --build --force-recreate'
    sh 'docker-compose -f docker-compose.test.yml down --remove-orphans'
}

def runDeploy() {
    echo "runDeploy base on branch=${env.BRANCH_NAME}"
    withCredentials([string(credentialsId: SHUB_APIKEY_CREDENTIAL_ID, variable: 'SHUB_APIKEY')]) {
        execAnsiblePlaybook("-i servers/${env.BRANCH_NAME} -v deploy.yml")
    }
}

def setupDeployEnv() {
    withPythonEnv('python') {
        sh 'pip install -r requirements-deploy.txt'
    }
}

def execAnsiblePlaybook(argv) {
    withPythonEnv('python') {
        dir('playbooks') {
            sh "ansible-playbook ${argv}"
        }
    }
}


def onSuccess(stage) {
    def info = "${stage} Success"
    // notifySlackStatus(STATUS_SUCCESS, info)
}

def onFail(stage) {
    def info = "${stage} Failure"
    // notifySlackStatus(STATUS_FAILURE, info)
}

def notifySlackStatus(status, info) {
    def duration = getBuildDuration()
    def message = "${env.JOB_NAME} - ${env.BUILD_DISPLAY_NAME} (${env.git_commit_short}) ${info} after ${duration} (<${env.BUILD_URL}|URL>)"
    echo message

    def color = ''
    if(status == STATUS_SUCCESS) {
        color = COLOR_OK
    }
    else {
        color = COLOR_ERROR
    }
    slackSend(color: color, message: message)
}

def getBuildDuration() {
    def duration = System.currentTimeMillis() - currentBuild.startTimeInMillis
    def sec = (duration / 1000).intValue() % 60
    def min = (duration / (1000*60)).intValue() % 60
    def hr = (duration / (1000*60*60)).intValue() % 24
    if(hr > 0) {
        return "${hr} hours ${min} min ${sec} sec"
    }
    else{
        return "${min} min ${sec} sec"
    }
}
