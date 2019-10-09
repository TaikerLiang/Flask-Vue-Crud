#!/usr/bin/env groovy
import groovy.transform.Field


@Field def SHUB_APIKEY_CREDENTIAL_ID = 'scrapinghub-hardcore-apikey'

@Field def SLACK_CHANNEL = '#jenkins-feed-edi'

@Field def STATUS_SUCCESS = 'Success'
@Field def STATUS_FAILURE = 'Failure'

@Field def COLOR_OK = '#36A64F'
@Field def COLOR_ERROR = '#D00000'
@Field def COLOR_WARNING = '#DAA038'


pipeline {
    agent any
    environment {
        GIT_COMMIT_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
    }
    stages {
        stage('Test') {
            agent {
                docker {
                    image 'python:3.7'
                }
            }
            when {
                anyOf {
                    branch 'develop'
                    branch 'stage'
                    branch 'master'
                    changeRequest()
                }
            }
            environment {
                HOME = "$WORKSPACE"
                PYTHONDONTWRITEBYTECODE = 1
                PYTHONUNBUFFERED = 1
            }
            steps {
                runTest()
            }
            post {
                always {
                    junit 'pytest_report.xml'
                    cobertura coberturaReportFile: 'pytest_coverage.xml'
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
            when {
                anyOf {
                    branch 'stage'
                    branch 'master'
                }
            }
            steps {
                setupDevEnv()
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
    def userPipPackageBase = sh([returnStdout: true, script: 'python -m site --user-base']).trim()
    echo "userPipPackageBase=${userPipPackageBase}"

    sh "pip install -e '.[dev]' --user --no-cache"
    sh "${userPipPackageBase}/bin/epsc test --pytest-args='-p no:cacheprovider --junitxml=pytest_report.xml --cov=src/ --cov-report=xml:pytest_coverage.xml'"
}

def runDeploy() {
    echo "runDeploy base on branch=${BRANCH_NAME}"
    withCredentials([string(credentialsId: SHUB_APIKEY_CREDENTIAL_ID, variable: 'SHUB_APIKEY')]) {
        execAnsiblePlaybook("-i servers/${BRANCH_NAME} -v deploy.yml")
    }
}

def setupDevEnv() {
    withPythonEnv('python') {
        sh 'pip install -r requirements-dev.txt'
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
    notifySlackStatus(STATUS_SUCCESS, info)
}

def onFail(stage) {
    def info = "${stage} Failure"
    notifySlackStatus(STATUS_FAILURE, info)
}

def notifySlackStatus(status, info) {
    def duration = getBuildDuration()
    def color = (status == STATUS_SUCCESS) ? COLOR_OK : COLOR_ERROR
    def message = "${JOB_NAME} - ${BUILD_DISPLAY_NAME} (${GIT_COMMIT_SHORT}) ${info} after ${duration} (<${BUILD_URL}|URL>)"
    echo message

    slackSend([channel: SLACK_CHANNEL, color: color, message: message])
}

def getBuildDuration() {
    def duration = System.currentTimeMillis() - currentBuild.startTimeInMillis
    def sec = (duration / 1000).intValue() % 60
    def min = (duration / (1000*60)).intValue() % 60
    def hr = (duration / (1000*60*60)).intValue() % 24

    if (hr > 0) {
        return "${hr} hours ${min} min ${sec} sec"
    } else {
        return "${min} min ${sec} sec"
    }
}
