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
                        env.project_name=projectConfig.project_name
                        env.image_registry=projectConfig.image_registry
                        env.docker_cred_username=projectConfig.docker_cred_username
                        env.docker_cred_password=projectConfig.docker_cred_password
                        servicesToCheck = projectConfig.services

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
                stage("install the dependencies first"){
                    steps{
                        script{
                            installAppDependencies(env.DETECTED_LANG)
                        }
                    }
                }
                stage("Linting (App Code, Terraform, Kubernetes, Docker)") {
                    steps {
                        runLinter(env.DETECTED_LANG)
                        // runInfrastructureLinting('terraform/')
                        // runKubernetesLinting('kubernetes/') 
                        // validateDockerImage('Dockerfile')
                    }
                }
                // stage("Secrets Detection") {
                //     steps {
                //         performSecretsDetection('.') // Scan the entire workspace
                //     }
                // }
                stage("Install Dependencies and dependency scanning and type checking and unit tests and code coverage calcualtion ") {
                    steps {
                        // performDependencyScan(env.DETECTED_LANG)
                        runTypeChecks(env.DETECTED_LANG)
                        runUnitTests(env.DETECTED_LANG)
                        calculateCodeCoverage(env.DETECTED_LANG)
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
                stage("Building the Application") {
                    steps {
                        buildApplication(env.DETECTED_LANG)
                    }
                }
                stage("Mutation Testing and snapshot and component testing at Dev") {
                    steps {
                        runMutationTests(env.DETECTED_LANG)
                        runSnapshotTests(env.DETECTED_LANG)
                        runComponentTests(env.DETECTED_LANG)
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
                stage("Deploy to Dev") {
                    steps {
                        script {
                            try {
                                withKubeConfig(
                                    credentialsId: env.kubernetesCredentialsId,
                                    serverUrl: env.kubernetes_endpoint,
                                    namespace: "${env.BRANCH_NAME}",
                                    contextName: '',
                                    restrictKubeConfigAccess: false
                                ) {
                                    dir("kubernetes") {  // 👈 Change this to your folder name
                                        sh """ 
                                        helm upgrade --install ${env.service_name} . \
                                            -f values-${env.BRANCH_NAME}.yaml \
                                            --set ${env.service_name}.image=${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version} \
                                            --namespace ${env.BRANCH_NAME} 
                                        """
                                    }
                                }
                            } catch (err) {
                                echo "Failed to deploy to the dev environment: ${err}"
                                error("Stopping pipeline")
                            }
                        }
                    }
                }
                stage("checking the services that are running or not") {
                    steps {
                        script {
                            try {
                                withKubeConfig(
                                    credentialsId: env.kubernetesCredentialsId,
                                    serverUrl: env.kubernetes_endpoint,
                                    namespace: "${env.BRANCH_NAME}",
                                    contextName: '',
                                    restrictKubeConfigAccess: false
                                ) {
                                    dir("kubernetes") {  // 👈 Change this to your folder name
                                        checkk8services(servicesToCheck, "${env.BRANCH_NAME}")
                                    }
                                }
                            } catch (err) {
                                echo "services are not running : ${err}"
                                error("Stopping pipeline")
                            }
                        }
                    }
                }
                stage("Perform Smoke Testing and sanity testing and APi testing and integratio testing andlight ui test and regression testing feature flag and chaos and security After Dev Deploy") {
                    steps {
                        performSmokeTesting(env.DETECTED_LANG)
                        performSanityTesting(env.DETECTED_LANG)
                        performApiTesting(env.DETECTED_LANG)
                        performIntegrationTesting(env.DETECTED_LANG)
                        performDatabaseTesting(env.DETECTED_LANG)
                        performLightUiTests(env.DETECTED_LANG)
                        performRegressionTesting(env.DETECTED_LANG)
                        performFeatureFlagChecks(env.DETECTED_LANG)
                        performSecurityChecks(env.DETECTED_LANG)
                        performChaosTestingAfterDeploy(env.DETECTED_LANG)
                        performLoadPerformanceTesting(env.DETECTED_LANG)
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
                stage("Building the Application") {
                    steps {
                        buildApplication(env.DETECTED_LANG)
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
                stage("install the dependencies first"){
                    steps{
                        script{
                            installAppDependencies(env.DETECTED_LANG)
                        }
                    }
                }
                stage("Linting (App Code, Terraform, Kubernetes, Docker)") {
                    steps {
                        runLinter(env.DETECTED_LANG)
                        // runInfrastructureLinting('terraform/')
                        // runKubernetesLinting('kubernetes/') 
                        // validateDockerImage('Dockerfile')
                    }
                }
                // stage("Secrets Detection") {
                //     steps {
                //         performSecretsDetection('.') // Scan the entire workspace
                //     }
                // }
                stage("Install Dependencies and dependency scanning and type checking and unit tests and code coverage calcualtion ") {
                    steps {
                        // performDependencyScan(env.DETECTED_LANG)
                        runTypeChecks(env.DETECTED_LANG)
                        runUnitTests(env.DETECTED_LANG)
                        calculateCodeCoverage(env.DETECTED_LANG)
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
                stage("Building the Application") {
                    steps {
                        buildApplication(env.DETECTED_LANG)
                    }
                }
                stage("Mutation Testing and snapshot and component testing at Dev") {
                    steps {
                        runMutationTests(env.DETECTED_LANG)
                        runSnapshotTests(env.DETECTED_LANG)
                        runComponentTests(env.DETECTED_LANG)
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
                        buildDockerImage("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}",env.version, '.')
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
                stage("Deploy to test environment") {
                    steps {
                        script {
                            try {
                                withKubeConfig(
                                    credentialsId: env.kubernetesCredentialsId,
                                    serverUrl: env.kubernetes_endpoint,
                                    namespace: "${env.BRANCH_NAME}",
                                    contextName: '',
                                    restrictKubeConfigAccess: false
                                ) {
                                    dir("kubernetes") {  // 👈 Change this to your folder name
                                        sh """ 
                                        helm upgrade --install ${env.service_name} . \
                                            -f values-${env.BRANCH_NAME}.yaml \
                                            --set ${env.service_name}.image=${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version} \
                                            --namespace ${env.BRANCH_NAME}
                                        """
                                    }
                                }
                            } catch (err) {
                                echo "Failed to deploy to the dev environment: ${err}"
                                error("Stopping pipeline")
                            }
                        }
                    }
                }
                stage("checking the services that are running or not") {
                    steps {
                        script {
                            try {
                                withKubeConfig(
                                    credentialsId: env.kubernetesCredentialsId,
                                    serverUrl: env.kubernetes_endpoint,
                                    namespace: "${env.BRANCH_NAME}",
                                    contextName: '',
                                    restrictKubeConfigAccess: false
                                ) {
                                    dir("kubernetes") {  // 👈 Change this to your folder name
                                        checkk8services(servicesToCheck, "${env.BRANCH_NAME}")
                                    }
                                }
                            } catch (err) {
                                echo "services are not running : ${err}"
                                error("Stopping pipeline")
                            }
                        }
                    }
                }
                stage("Smoke Test and sanity and integration and functional and api and regression in Test Env") {
                    steps {
                        performSmokeTesting(env.DETECTED_LANG)
                        performSanityTesting(env.DETECTED_LANG)
                        performIntegrationTesting(env.DETECTED_LANG)
                        performApiTesting(env.DETECTED_LANG)
                        performDatabaseTesting(env.DETECTED_LANG)
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
                stage("install the dependencies first"){
                    steps{
                        script{
                            installAppDependencies(env.DETECTED_LANG)
                        }
                    }
                }
                stage("Linting (App Code, Terraform, Kubernetes, Docker)") {
                    steps {
                        runLinter(env.DETECTED_LANG)
                        // runInfrastructureLinting('terraform/')
                        // runKubernetesLinting('kubernetes/') 
                        // validateDockerImage('Dockerfile')
                    }
                }
                // stage("Secrets Detection") {
                //     steps {
                //         performSecretsDetection('.') // Scan the entire workspace
                //     }
                // }
                stage("Install Dependencies and dependency scanning and type checking and unit tests and code coverage calcualtion ") {
                    steps {
                        // performDependencyScan(env.DETECTED_LANG)
                        runTypeChecks(env.DETECTED_LANG)
                        runUnitTests(env.DETECTED_LANG)
                        calculateCodeCoverage(env.DETECTED_LANG)
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
                stage("Building the Application") {
                    steps {
                        buildApplication(env.DETECTED_LANG)
                    }
                }
                stage("Mutation Testing and snapshot and component testing at Dev") {
                    steps {
                        runMutationTests(env.DETECTED_LANG)
                        runSnapshotTests(env.DETECTED_LANG)
                        runComponentTests(env.DETECTED_LANG)
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
                stage("Perform build and   docker linting Container Scanning using trivy and syft and docker scout and Dockle and snyk at Test Env") {
                    steps {
                        buildDockerImage("${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}", env.version, '.')
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
               stage("Deploy to Dev") {
                    steps {
                        script {
                            try {
                                withKubeConfig(
                                    credentialsId: env.kubernetesCredentialsId,
                                    serverUrl: env.kubernetes_endpoint,
                                    namespace: "${env.BRANCH_NAME}",
                                    contextName: '',
                                    restrictKubeConfigAccess: false
                                ) {
                                    dir("kubernetes") {  // 👈 Change this to your folder name
                                        sh """ 
                                        helm upgrade --install ${env.service_name} . \
                                            -f values-${env.BRANCH_NAME}.yaml \
                                            --set ${env.service_name}.image=${env.docker_username}/${env.service_name}-${env.BRANCH_NAME}:${env.version} \
                                            --namespace ${env.BRANCH_NAME}
                                        """
                                    }
                                }
                            } catch (err) {
                                echo "Failed to deploy to the dev environment: ${err}"
                                error("Stopping pipeline")
                            }
                        }
                    }
                }
                stage("checking the services that are running or not") {
                    steps {
                        script {
                            try {
                                withKubeConfig(
                                    credentialsId: env.kubernetesCredentialsId,
                                    serverUrl: env.kubernetes_endpoint,
                                    namespace: "${env.BRANCH_NAME}",
                                    contextName: '',
                                    restrictKubeConfigAccess: false
                                ) {
                                    dir("kubernetes") {  // 👈 Change this to your folder name
                                        checkproduction(servicesToCheck, "${env.BRANCH_NAME}","${env.notificationRecipients}")
                                    }
                                }
                            } catch (err) {
                                echo "services are not running : ${err}"
                                error("Stopping pipeline")
                            }
                        }
                    }
                }
                stage("Smoke Test and sanity test and synthatic test and  in preProduction") {
                    steps {
                        performSmokeTesting(env.DETECTED_LANG)
                        performSanityTesting(env.DETECTED_LANG)
                        performIntegrationTesting(env.DETECTED_LANG)
                        performApiTesting(env.DETECTED_LANG)
                        performRegressionTesting(env.DETECTED_LANG)
                        performDatabaseTesting(env.DETECTED_LANG)
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