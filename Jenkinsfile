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
        stage('Test') {
            when {
                anyOf {
                    branch 'develop'
                    branch 'stage'
                    branch 'master'
                    changeRequest()
                }
            }
            docker {
                image 'python:3.7'
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
    def userPipPackageBase = sh([returnStdout: true, script: 'python -m site --user-base']).trim()
    echo "userPipPackageBase=${userPipPackageBase}"

    sh "pip install -e '.[dev,tests]' --user --no-cache"
    sh "${userPipPackageBase}/bin/mycli test --pytest-args='-p no:cacheprovider --junitxml=pytest_report.xml --cov=src/ --cov-report=xml:pytest_coverage.xml'"
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
