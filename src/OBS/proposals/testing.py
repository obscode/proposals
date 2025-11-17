# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import OBS.proposals


class ObsProposalsLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.app.dexterity

        self.loadZCML(package=plone.app.dexterity)
        import plone.restapi

        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=OBS.proposals)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "OBS.proposals:default")


OBS_PROPOSALS_FIXTURE = ObsProposalsLayer()


OBS_PROPOSALS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(OBS_PROPOSALS_FIXTURE,),
    name="ObsProposalsLayer:IntegrationTesting",
)


OBS_PROPOSALS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(OBS_PROPOSALS_FIXTURE,),
    name="ObsProposalsLayer:FunctionalTesting",
)


OBS_PROPOSALS_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        OBS_PROPOSALS_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name="ObsProposalsLayer:AcceptanceTesting",
)
