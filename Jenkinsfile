def runAutomationJob(testBranch, mvRetailBranch, mvNextBranch) {
    script {
        def root_message = slackSend(
            botUser: true,
            color: 'warning',
            channel: 'automation-jobs',
            message:  "RUNNING: ${testBranch} against ${mvRetailBranch} and ${mvNextBranch} - (<${env.RUN_DISPLAY_URL}|Open>)",
            tokenCredentialId: 'automationSlackBot'
        )

        def finished_job = build job: '/automation/automaton', propagate: false, parameters: [
            string(name: 'MVRETAIL_BRANCH', value: mvRetailBranch),
            string(name: 'MVNEXT_BRANCH', value: mvNextBranch),
            string(name: 'TESTS_BRANCH', value: testBranch)
        ]
        sleep(5)
        copyArtifacts(
            projectName: '/automation/automaton',
            selector: specific("${finished_job.number}"),
            target: "${env.WORKSPACE}/",
            filter: "*.txt"
        )

        def result_color = 'good'
        def result_message = "PASS: ${testBranch} against ${mvRetailBranch} and ${mvNextBranch} - (<${finished_job.absoluteUrl}|Open>) \n"
        if (finished_job.result == 'FAILURE') {
            result_color = 'danger'
            result_message = "FAIL: ${testBranch} against ${mvRetailBranch} and ${mvNextBranch} - (<${finished_job.absoluteUrl}|Open>) \n"
            slackUploadFile(
                filePath: "results.txt",
                channel: 'automation-jobs:' + root_message.ts,
                initialComment:  "Results:",
                credentialId: 'automationSlackBot'
            )
        }
        slackSend(
            botUser: true,
            color: result_color,
            channel: root_message.channelId,
            message:  result_message,
            timestamp: root_message.ts,
            tokenCredentialId: 'automationSlackBot'
        )
        if (finished_job.result == 'FAILURE') {
            error("Automated tests have found issues.  Consult with automation personnel for next steps")
        }
    }
}

pipeline {
    agent none
    options { buildDiscarder(logRotator(numToKeepStr: '10')) }
    stages {
        stage('Master branch build') {
            agent any

            when {
                beforeAgent true
                branch 'master*'
                not {
                    triggeredBy 'BranchIndexingCause'
                }
            }
            steps {
                runAutomationJob(env.BRANCH_NAME, 'developer', ' released')
            }
        }
        stage('PR Build') {
            agent any
            when {
                beforeAgent true
                changeRequest()
                not {
                    triggeredBy 'BranchIndexingCause'
                }
            }
            steps {
                runAutomationJob(env.CHANGE_BRANCH, 'developer', 'released')
            }
        }

        }
    }
