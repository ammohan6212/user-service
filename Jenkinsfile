@Library('microservice@main') _ 

pipeline {
    agent any
    options {
        disableConcurrentBuilds()
        // skipDefaultCheckout true
    }
    stages {
        stage("Load project configuration"){
            steps{
                script{
                    def projectConfig = readJSON file: 'config.json'
                        env.github_repo=projectConfig.github_repo
                        env.service_name = projectConfig.serviceName
                        env.notificationRecipients = projectConfig.notificationRecipients
                        env.docker_username=projectConfig.docker_username
                        env.kubernetes_endpoint=projectConfig.kubernetes_endpoint
                        env.bucket_name=projectConfig.bucket_name  
                        env.docker_credentials=projectConfig.docker_credentials
                        env.docker_registry=projectConfig.docker_registry
                        env.kubernetesClusterName=projectConfig.kubernetesClusterName
                        env.kubernetesCredentialsId=projectConfig.kubernetesCredentialsId
                        env.kubernetesCaCertificate=projectConfig.kubernetesCaCertificate
                        env.gcp_credid=projectConfig.gcp_credid
                        env.aws_credid=projectConfig.aws_credid
                        env.service_port=projectConfig.service_port
                        env.project_name=projectConfig.project_name
                        env.image_registry=projectConfig.image_registry
                        env.docker_cred_username=projectConfig.docker_cred_username
                        env.docker_cred_password=projectConfig.docker_cred_password
                }
            }
        }
        stage("Development Workflow") {
            agent { label 'agent'}
            when {
                branch 'dev'
            }
            stages {
                stage("Clone Dev Repo & Get Version and detect the language") {
                    steps {
                        script{
                            cloneRepoAndGetVersion(env.BRANCH_NAME, env.github_repo)
                            detectLanguage() 
                        }
                    }
                }
                // stage("Linting the Code and terraform linting and kubernetes linting and  docker linting") {
                //     steps {
                //         runLinter(env.DETECTED_LANG)
                //         runInfrastructureLinting('terraform/')
                //         runKubernetesLinting('kubernetes/') 
                //         validateDockerImage('Dockerfile')
                //     }
                // }
                // stage("Secrets Detection") {
                     
                //     steps {
                //         performSecretsDetection('.') // Scan the entire workspace
                //     }
                // }
                stage("Install Dependencies and dependency scanning and type checking and unit tests and code coverage calcualtion ") {
                    steps {
                        installAppDependencies(env.DETECTED_LANG)
                        // performDependencyScan(env.DETECTED_LANG)
                        // runTypeChecks(env.DETECTED_LANG)
                        // runUnitTests(env.DETECTED_LANG)
                        // calculateCodeCoverage(env.DETECTED_LANG)
                    }
                }
                // stage("perform sonarqube scans"){
                //     steps{     
                //         echo "sonarqube test happens here" 
                //         runSonarQubeScan(env.SONAR_PROJECT_KEY)
                //     }
                // }
                // stage("Check SonarQube Quality Gate") {
                //     steps {
                //         waitForQualityGate abortPipeline: true
                //     }
                // }
                // stage("Mutation Testing and snapshot and component testing at Dev") {
                //     steps {
                //         runMutationTests(env.DETECTED_LANG)
                //         runSnapshotTests(env.DETECTED_LANG)
                //         runComponentTests(env.DETECTED_LANG)
                //     }
                // }
                stage("Building the Application") {
                    steps {
                        buildApplication(env.DETECTED_LANG)
                    }
                }
                stage("Create Archiving File and push the artifact ") {
                        steps {
                            script {
                                try {
                                    createArchive("${env.service_name}-${env.BRANCH_NAME}-${env.version}.zip", 'src/')
                                    pushArtifact("${env.service_name}-${env.BRANCH_NAME}-${env.version}.zip","gs://${env.bucket_name}/artifacts","gcp-credentials-id")
                                } catch (err) {
                                    echo "failed to push the artifact to specific repository ${err}"
                                    error("Stopping pipeline")
                                }
                            }
                        }
                }
                stage("Perform building and  docker linting Container Scanning using trivy and syft and docker scout and Dockle and snyk at Test Env") {
                    steps {
                        buildDockerImage("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}", env.version, '.')
                        validateDockerImagedockle("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}")
                        scanContainerTrivy("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}")
                        scanContainerSyftDockle("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}")
                        scanContainerSnyk("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}", "Dockerfile")
                        scanContainerDockerScout("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}", "${env.docker_cred_username}", "${env.docker_cred_password}")
                        scanContainerGrype("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}")
                    }
                }
                stage("Perform Integration and ui/component testingand static security analysis and chaos testing with Docker Containers") {
                    steps {
                        integrationWithDocker()
                        runUiComponentTests(env.DETECTED_LANG)
                        performStaticSecurityAnalysis(env.DETECTED_LANG)
                        runChaosTests(env.DETECTED_LANG)
                    }
                }
                stage("Push Docker Image to dev env Registry") {
                    steps {
                        script { // Wrap the steps in a script block to use try-catch
                            try {
                                pushDockerImageToRegistry("${env.image_registry}","${env.docker_cred_username}","${env.docker_cred_password}", "${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}") // Corrected DOCKER_USERNAME to docker_username 
                            } catch (err) {
                                echo "Failed to push Docker image to registry: ${err.getMessage()}"
                                error("Stopping pipeline due to Docker image push failure.")
                            }
                        }
                    }
                }
                // stage("Deploy to Dev") {
                //     steps {
                //         script {
                //             try {
                //                 withKubeConfig(
                //                     caCertificate: env.kubernetesCaCertificate,clusterName: env.kubernetesClusterName,contextName: '',credentialsId: env.kubernetesCredentialsId,namespace: "${env.BRANCH_NAME}",restrictKubeConfigAccess: false,serverUrl: env.kubernetes_endpoint
                //                 ) {
                //                     // Change Kubernetes service selector to route traffic to Green
                //                     sh """kubectl apply -f ${env.service_name}-deployment.yml -n ${env.BRANCH_NAME}"""
                //                 }
                //             } catch (err) {
                //                 echo "failed to deploy to the production ${err}"
                //                 error("Stopping pipeline")
                //             }
                //         }
                //     }
                // }
                stage("Perform Smoke Testing and sanity testing and APi testing and integratio testing andlight ui test and regression testing feature flag and chaos and security After Dev Deploy") {
                    steps {
                        performSmokeTesting(env.DETECTED_LANG)
                        performSanityTesting(env.DETECTED_LANG)
                        performApiTesting(env.DETECTED_LANG)
                        performIntegrationTesting(env.DETECTED_LANG)
                        performDatabaseTesting()
                        // performLightUiTests(env.DETECTED_LANG)
                        // performRegressionTesting(env.DETECTED_LANG)
                        // performFeatureFlagChecks(env.DETECTED_LANG)
                        // performSecurityChecks(env.DETECTED_LANG)
                        // performChaosTestingAfterDeploy(env.DETECTED_LANG)
                        // performLoadPerformanceTesting(env.DETECTED_LANG)
                    }
                }                
                stage("Perform Logging and Monitoring Checks After Dev Deploy") {
                    steps {
                        performLoggingMonitoringChecks()
                    }
                }
                stage("Generate Version File Dev Env") {
                    steps {
                        generateVersionFile('gcp', "${env.bucket_name}/version-files/", "${gcp_credid}")
                    }
                }
            }
        }
        stage("bugfix workflow Workflow") {
            when {
                branch pattern: "bugfix/.*", comparator: "REGEXP"
            }
            stages {
                stage("Clone Dev Repo & Get Version and detect the language") {
                    steps {
                        script{
                            cloneRepoAndGetVersion(env.BRANCH_NAME, env.github_repo)
                            detectLanguage() 
                        }
                    }
                }
                stage("Install Dependencies and dependency scanning and type checking and unit tests and code coverage calcualtion ") {
                    steps {
                        runLinter(env.DETECTED_LANG)
                        performSecretsDetection('.')
                        installAppDependencies(env.DETECTED_LANG)
                        performDependencyScan(env.DETECTED_LANG)
                        runTypeChecks(env.DETECTED_LANG)
                        runUnitTests(env.DETECTED_LANG)
                        calculateCodeCoverage(env.DETECTED_LANG)
                    }
                }
                stage("perform sonarqube scans"){
                    steps{      
                        runSonarQubeScan(env.SONAR_PROJECT_KEY)
                    }
                }
                stage("Check SonarQube Quality Gate") {
                    steps {
                        waitForQualityGate abortPipeline: true
                    }
                }
                stage("sonarqube and Mutation Testing and snapshot and component testing at Dev") {
                    steps {
                        runMutationTests(env.DETECTED_LANG)
                        runSnapshotTests(env.DETECTED_LANG)
                        runComponentTests(env.DETECTED_LANG)
                        performRegressionTesting(env.DETECTED_LANG)
                    }
                }
                stage("Building the Application") {
                    steps {
                        buildApplication(env.DETECTED_LANG)
                    }
                }    
                stage("Create Archiving File and push the artifact ") {
                    steps {
                        script {
                            try {
                                createArchive("${env.service_name}-${env.BRANCH_NAME}-${env.version}.zip", 'src/')
                                pushArtifact("${env.service_name}-${env.BRANCH_NAME}-${env.version}.zip","gs://${env.bucket_name}/artifacts","gcp-credentials-id")
                            } catch (err) {
                                echo "failed to push the artifact to specific repository ${err}"
                                error("Stopping pipeline")
                            }
                        }
                    }
                }                    
            }
        }
        stage("feature branch workflow Workflow") {
            agent { label 'agent'}
            when {
                branch pattern: "feature/.*", comparator: "REGEXP"
            }
            stages {
                stage("Clone Dev Repo & Get Version and detect the language") {
                    steps {
                        script{
                            cloneRepoAndGetVersion(env.BRANCH_NAME, env.github_repo)
                            detectLanguage() 
                        }
                    }
                }
                stage("Install Dependencies and dependency scanning and type checking and unit tests and code coverage calcualtion ") {
                    steps {
                        runLinter(env.DETECTED_LANG)
                        performSecretsDetection('.')
                        installAppDependencies(env.DETECTED_LANG)
                        performDependencyScan(env.DETECTED_LANG)
                        runTypeChecks(env.DETECTED_LANG)
                        runUnitTests(env.DETECTED_LANG)
                        calculateCodeCoverage(env.DETECTED_LANG)
                    }
                }
                // stage("perform sonarqube scans"){
                //     steps{      
                //         runSonarQubeScan(env.SONAR_PROJECT_KEY)
                //     }
                // }
                // stage("Check SonarQube Quality Gate") {
                //     steps {
                //         waitForQualityGate abortPipeline: true
                //     }
                // }
                stage("sonarqube and Mutation Testing and snapshot and component testing at Dev") {
                    steps {
                        runMutationTests(env.DETECTED_LANG)
                        runSnapshotTests(env.DETECTED_LANG)
                        runComponentTests(env.DETECTED_LANG)
                        performRegressionTesting(env.DETECTED_LANG)
                    }
                }
                stage("Building the Application") {
                    steps {
                        buildApplication(env.DETECTED_LANG)
                    }
                }    
                stage("Create Archiving File and push the artifact ") {
                    steps {
                        script {
                            try {
                                createArchive("${env.service_name}-${env.BRANCH_NAME}-${env.version}.zip", 'src/')
                                pushArtifact("${env.service_name}-${env.BRANCH_NAME}-${env.version}.zip","gs://${env.bucket_name}/artifacts","gcp-credentials-id")
                            } catch (err) {
                                echo "failed to push the artifact to specific repository ${err}"
                                error("Stopping pipeline")
                            }
                        }
                    }
                }
            }
        }
        stage("Test Environment Workflow") {
            agent { label 'agent'}
            when {
                branch 'test'
            }
            stages {
                stage("Clone Dev Repo & Get Version and detect the language") {
                    steps {
                        script{
                            cloneRepoAndGetVersion(env.BRANCH_NAME, env.github_repo)
                            detectLanguage() 
                        }
                    }
                }
                stage("Install Dependencies and dependency scanning and type checking and unit tests and code coverage calcualtion ") {
                    steps {
                        runLinter(env.DETECTED_LANG)
                        performSecretsDetection('.')
                        installAppDependencies(env.DETECTED_LANG)
                        performDependencyScan(env.DETECTED_LANG)
                        runTypeChecks(env.DETECTED_LANG)
                        runUnitTests(env.DETECTED_LANG)
                        calculateCodeCoverage(env.DETECTED_LANG)
                    }
                }
                // stage("perform sonarqube scans"){
                //     steps{      
                //         runSonarQubeScan(env.SONAR_PROJECT_KEY)
                //     }
                // }
                // stage("Check SonarQube Quality Gate") {
                //     steps {
                //         waitForQualityGate abortPipeline: true
                //     }
                // }
                stage("Create Archiving File and push the artifact ") {    
                    steps {
                        script {
                            try {
                                createArchive("${env.service_name}-${env.BRANCH_NAME}-${env.version}.zip", 'src/')
                                pushArtifact("${env.service_name}-${env.BRANCH_NAME}-${env.version}.zip","gs://${env.bucket_name}/artifacts","gcp-credentials-id")
                            } catch (err) {
                                echo "failed to push the artifact to specific repository ${err}"
                                error("Stopping pipeline")
                            }
                        }
                    }
                }
                stage("Perform building and  docker linting Container Scanning using trivy and syft and docker scout and Dockle and snyk at Test Env") {
                    steps {
                        buildDockerImage("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}", env.VERSION_TAG, '.')
                        validateDockerImage("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}")
                        scanContainerTrivy("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}")
                        scanContainerSyftDockle("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}")
                        scanContainerSnyk("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}", "Dockerfile")
                        scanContainerDockerScout("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}", "${env.docker_cred_username}", "${env.docker_cred_password}")
                        scanContainerGrype("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}")
                    }
                }
                stage("Push Docker Image to test env Registry") {
                    steps {
                        script { // Wrap the steps in a script block to use try-catch
                            try {
                                pushDockerImageToRegistry("${env.image_registry}","${env.docker_cred_username}","${env.docker_cred_password}", "${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}") // Corrected DOCKER_USERNAME to docker_username 
                            } catch (err) {
                                echo "Failed to push Docker image to registry: ${err.getMessage()}"
                                error("Stopping pipeline due to Docker image push failure.")
                            }
                        }
                    }
                }
                // stage("Deploy to test") {
                //     steps {
                //         script {
                //             try {
                //                 withKubeConfig(
                //                     caCertificate: env.kubernetesCaCertificate,clusterName: env.kubernetesClusterName,contextName: '',credentialsId: env.kubernetesCredentialsId,namespace: "${env.BRANCH_NAME}",restrictKubeConfigAccess: false,serverUrl: env.kubernetes_endpoint
                //                 ) {
                //                     // Change Kubernetes service selector to route traffic to Green
                //                     sh """kubectl apply -f ${env.service_name}-deployment.yml -n ${env.BRANCH_NAME}"""
                //                 }
                //             } catch (err) {
                //                 echo "failed to deploy to the production ${err}"
                //                 error("Stopping pipeline")
                //             }
                //         }
                //     }
                // }
                stage("Smoke Test and sanity and integration and functional and api and regression in Test Env") {
                    steps {
                        performSmokeTesting(env.DETECTED_LANG)
                        performSanityTesting(env.DETECTED_LANG)
                        performIntegrationTesting(env.DETECTED_LANG)
                        performApiTesting(env.DETECTED_LANG)
                        performDatabaseTesting()
                        performRegressionTesting(env.DETECTED_LANG)
                        performLoadPerformanceTesting(env.DETECTED_LANG)
                        // performChaosTestingAfterDeploy(env.DETECTED_LANG)  ###this is optional here
                    }
                }
                stage("Generate Version File Test Env") {
                    steps {
                        generateVersionFile('gcp', "${env.bucket_name}/version-files/", "${gcp_credid}")
                    }
                }
                stage("Need the manual approval to complete the test env"){
                    steps{
                        sendEmailNotification('Alert', env.notificationRecipients)
                    }
                }
                stage("Approval for Test Success") {
                    steps {
                        script {
                            try {
                                input message: "Do you approve to proceed to Staging Environment?",
                                    ok: "Approve",
                                    submitter: "manager,admin"
                                echo "Approval granted. Proceeding to Staging Environment."
                                currentBuild.result = 'SUCCESS'
                            } catch (err) {
                                echo "Approval was not granted. Error: ${err}"
                                currentBuild.result = 'FAILURE'
                                error("Pipeline failed due to rejection or interruption.")
                            }
                        }
                    }
                }

            }
        }
        stage("deploying the application into prod"){
            agent { label 'agent'}
            when {
                branch 'main' // Or 'master'
            }
            stages{
                stage("Approval Before Deploying to Production") {
                    steps {
                        input message: "Do you approve deployment to Production?", ok: "Deploy Now", submitter: "manager,admin"
                    }
                }
                stage("create the change request containing what is changing and any DB changes and any downtime and rollback plan if deplyoment failes and deploymentwindow and stakeholders"){
                    steps{
                        script{
                            echo "create a change request for production deployment"
                        }
                    }
                }
                stage("Clone Dev Repo & Get Version and detect the language") {
                    steps {
                        script{
                            cloneRepoAndGetVersion(env.BRANCH_NAME, env.github_repo)
                            detectLanguage() 
                        }
                    }
                }
                stage("Install Dependencies and dependency scanning and type checking and unit tests and code coverage calcualtion ") {
                    steps {
                        runLinter(env.DETECTED_LANG)
                        performSecretsDetection('.')
                        installAppDependencies(env.DETECTED_LANG)
                        performDependencyScan(env.DETECTED_LANG)
                        runTypeChecks(env.DETECTED_LANG)
                        runUnitTests(env.DETECTED_LANG)
                        calculateCodeCoverage(env.DETECTED_LANG)
                    }
                }
                // stage("perform sonarqube scans"){
                //     steps{      
                //         runSonarQubeScan(env.SONAR_PROJECT_KEY)
                //     }
                // }
                // stage("Check SonarQube Quality Gate") {
                //     steps {
                //         waitForQualityGate abortPipeline: true
                //     }
                // }
                stage("Create Archiving File and push the artifact ") {
                    steps {
                        script {
                            try {
                                createArchive("${env.service_name}-${env.BRANCH_NAME}-${env.version}.zip", 'src/')
                                pushArtifact("${env.service_name}-${env.BRANCH_NAME}-${env.version}.zip","gs://${env.bucket_name}/artifacts","gcp-credentials-id")
                            } catch (err) {
                                echo "failed to push the artifact to specific repository ${err}"
                                error("Stopping pipeline")
                            }
                        }
                    }
                }
                stage("Perform build and   docker linting Container Scanning using trivy and syft and docker scout and Dockle and snyk at Test Env") {
                    steps {
                        buildDockerImage("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}", env.VERSION_TAG, '.')
                        validateDockerImage("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}")
                        scanContainerTrivy("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}")
                        scanContainerSyftDockle("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}")
                        scanContainerSnyk("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}", "Dockerfile")
                        scanContainerDockerScout("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}", "${env.docker_cred_username}", "${env.docker_cred_password}")
                        scanContainerGrype("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}")
                    }
                }
                stage("need approval to push the docker image to repository"){
                    steps{
                        script{
                            input message: "Do you approve image  to respository?", ok: "Deploy Now", submitter: "manager,admin"
                        }
                    }
                }
                stage("Push Docker Image to prod env Registry") {
                    steps {
                        script { // Wrap the steps in a script block to use try-catch
                            try {
                                pushDockerImageToRegistry("${env.image_registry}","${env.docker_cred_username}","${env.docker_cred_password}", "${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version}") // Corrected DOCKER_USERNAME to docker_username 
                            } catch (err) {
                                echo "Failed to push Docker image to registry: ${err.getMessage()}"
                                error("Stopping pipeline due to Docker image push failure.")
                            }
                        }
                    }
                }
                // stage("Deploy to prod at peak off-hours") {
                //     steps {
                //         script {
                //             try {
                //                 withKubeConfig(
                //                     caCertificate: env.kubernetesCaCertificate,clusterName: env.kubernetesClusterName,contextName: '',credentialsId: env.kubernetesCredentialsId,namespace: "${env.BRANCH_NAME}",restrictKubeConfigAccess: false,serverUrl: env.kubernetes_endpoint
                //                 ) {
                //                     sh """
                //                     kubectl apply -f ${service_name}-deployment.yaml -n ${env.BRANCH_NAME}
                //                     kubectl rollout status deployment/${service_name} -n ${env.BRANCH_NAME}
                //                     """
                //                 }
                //             } catch (err) {
                //                 echo "failed to deploy to the production ${err}"
                //                 error("Stopping pipeline")
                //             }
                //         }
                //     }
                // }
                // stage('Automated Post-Deployment Verification & Rollback') {
                //     steps {
                //         script {
                //             withKubeConfig(
                //                     caCertificate: env.kubernetesCaCertificate,clusterName: env.kubernetesClusterName,contextName: '',credentialsId: env.kubernetesCredentialsId,namespace: "${env.BRANCH_NAME}",restrictKubeConfigAccess: false,serverUrl: env.kubernetes_endpoint
                //                 ) {
                //                 def maxRetries = 5
                //                 def retryInterval = 30 // seconds
                //                 def deploymentHealthy = false

                //                 for (int i = 0; i < maxRetries; i++) {
                //                     try {
                //                         // Run health check inside cluster using ephemeral pod
                //                         def response = sh(
                //                             script: """
                //                             kubectl run tmp-shell --rm -i --tty --image=curlimages/curl --namespace ${env.BRANCH_NAME} -- /bin/sh -c "curl -o /dev/null -s -w '%{http_code}\\n' http://${env.service_name}.${env.BRANCH_NAME}.svc.cluster.local:${env.service_port}"
                //                             """,
                //                             returnStdout: true
                //                         ).trim()

                //                         if (response == '200') {
                //                             echo "✅ Application health check passed inside cluster."
                //                             deploymentHealthy = true
                //                             break
                //                         } else {
                //                             echo "⚠️ Application health check failed with status ${response}. Retrying in ${retryInterval} seconds..."
                //                         }
                //                     } catch (err) {
                //                         echo "⚠️ Health check command error: ${err.getMessage()}. Retrying in ${retryInterval} seconds..."
                //                     }
                //                     sleep retryInterval
                //                 }

                //                 if (!deploymentHealthy) {
                //                     echo "🔴 Automated health checks failed after multiple retries. Initiating rollback..."
                //                     try {
                //                         sh "kubectl rollout undo deployment/${env.service_name} -n ${env.BRANCH_NAME}"
                //                         echo "✅ Rollback command completed."
                //                     } catch (err) {
                //                         echo "❌ Rollback command failed: ${err.getMessage()}"
                //                     }
                //                     currentBuild.result = 'FAILURE'
                //                     error("🔴 Production deployment unhealthy. Automated rollback executed. Pipeline failed.")
                //                 } else {
                //                     echo "✅ Automated post-deployment verification passed."
                //                 }
                //             }
                //         }
                //     }
                // }
                stage("Smoke Test and sanity test and synthatic test and  in preProduction") {
                    steps {
                        performSmokeTesting(env.DETECTED_LANG)
                        performSanityTesting(env.DETECTED_LANG)
                        // performIntegrationTesting(env.DETECTED_LANG)
                        // performApiTesting(env.DETECTED_LANG)
                        performRegressionTesting(env.DETECTED_LANG)
                        performDatabaseTesting()
                        performChaosTestingAfterDeploy(env.DETECTED_LANG)
                    }
                }
                stage("is above tests and monitoring is fine for production environment"){
                    steps{
                        script{
                            input message: "Is prodiction environment is stable?", ok: "Deploy Now", submitter: "manager,admin"
                        }
                    }
                }
                stage("Generate Version File preprod Env") {
                    steps {
                        generateVersionFile('gcp', "${env.bucket_name}/version-files/", "${gcp_credid}")
                    }
                }
                stage("prod deployment is successful"){
                    steps{
                        script{
                            echo "the production deplyment successful"
                        }
                    }
                }
            }

        }
    }
    post {
        always {
            cleanWs() 
        }
        success {
            sendEmailNotification('SUCCESS', env.notificationRecipients)
        }
        unstable {
            sendEmailNotification('UNSTABLE', env.notificationRecipients)
        }
        failure {
            sendEmailNotification('FAILURE', env.notificationRecipients)
        }
        aborted {
            sendEmailNotification('ABORTED', env.notificationRecipients)
        }
    }
}