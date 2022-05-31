#!/usr/bin/env groovy
import groovy.transform.Field

@Field def SLACK_CHANNEL = '#edi-jenkins'

@Field def STATUS_SUCCESS = 'Success'
@Field def STATUS_FAILURE = 'Failure'

@Field def COLOR_OK = '#36A64F'
@Field def COLOR_ERROR = '#D00000'
@Field def COLOR_WARNING = '#DAA038'


pipeline {
    agent { node { label "hardcore-worker" } }
    stages {
        stage('Checkout') {
            steps {
                checkoutWithTags()
                script {
                    env.git_commit_short = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
                }
            }
        }
        stage('Build') {
            steps {
                runBuild()
            }
            post {
                success {
                    onSuccess('Build')
                }
                failure {
                    onFail('Build')
                }
            }
        }
        stage('Test') {
            steps {
                runTest()
            }
            post {
                success {
                    onSuccess('Test')
                }
                failure {
                    onFail('Test')
                }
            }
        }
        stage('Push') {
            when { expression { env.BRANCH_NAME in ['dockerize', 'develop', 'master', 'stage'] } }
            steps {
                runPush()
            }
            post {
                success {
                    onSuccess('Push')
                }
                failure {
                    onFail('Push')
                }
            }
        }
    }
}


//////////////////////////////////////////////////////////////////////////////////////////////
def checkoutWithTags() {
    checkout([
        $class: 'GitSCM',
        branches: scm.branches,
        extensions: scm.extensions + [[
            $class: 'CloneOption',
            noTags: false,
            reference: '',
            shallow: true,

            // default depth is 1, which will make "git describe" fail to get right tag
            // so we add a rough buffer here
            // to make sure travel at most 300 commits depth, we can find the latest tag
            depth: 300,
        ]],
        doGenerateSubmoduleConfigurations: scm.doGenerateSubmoduleConfigurations,
        userRemoteConfigs: scm.userRemoteConfigs,
    ])
}

def runBuild() {
    def scriptPath = 'docker/bin'
    try {
        dir(scriptPath) {
            sh './build.sh'
        }
    }
    catch (Exception e) {
        throw e
    }
}

def runPush() {
    def scriptPath = 'docker/bin'
    try {
        dir(scriptPath) {
            sh './push-ecr.sh'
        }
    }
    catch (Exception e) {
        throw e
    }
}

def runTest() {
    def scriptPath = 'docker/bin'
    try {
        dir(scriptPath) {
            sh './run-test.sh'
        }
    }
    catch (Exception e) {
        throw e
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
    def message = "${JOB_NAME} - ${BUILD_DISPLAY_NAME} (${env.git_commit_short}) ${info} after ${duration} (<${BUILD_URL}|URL>)"
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
