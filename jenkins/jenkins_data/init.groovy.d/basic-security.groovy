#!groovy
import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()

println "--> Skipping setup wizard"
instance.setInstallState(InstallState.INITIAL_SETUP_COMPLETED)

println "--> Creating local admin user"
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount("admin", "admin")
instance.setSecurityRealm(hudsonRealm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

instance.save()
