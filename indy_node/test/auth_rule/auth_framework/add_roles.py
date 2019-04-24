import pytest

from indy_common.authorize.auth_actions import AuthActionAdd, ADD_PREFIX, AbstractAuthAction, split_action_id
from indy_common.authorize.auth_constraints import AuthConstraint, IDENTITY_OWNER
from indy_common.authorize import auth_map
from indy_common.constants import NYM, ROLE, TRUST_ANCHOR, NETWORK_MONITOR
from indy_node.test.auth_rule.auth_framework.basic import AbstractTest, roles_to_string
from indy_node.test.auth_rule.helper import create_verkey_did, generate_auth_rule_operation
from plenum.common.constants import STEWARD, TRUSTEE
from plenum.common.exceptions import RequestRejectedException
from plenum.test.helper import sdk_multi_sign_request_objects, sdk_send_signed_requests, sdk_get_and_check_replies, \
    sdk_gen_request


class AddNewRoleTest(AbstractTest):
    def __init__(self, action_id: str, creator_wallet, env):
        self.action_id = action_id
        self.action = split_action_id(action_id)
        self.role = self.action.new_value
        self.role_string = roles_to_string[self.role]
        self.creator_wallet = creator_wallet
        self.trustee_wallet = env.sdk_wallet_trustee
        self.looper = env.looper
        self.sdk_pool_handle = env.sdk_pool_handle

        self.reqs = []
        self.auth_rule_reqs = []

    def prepare(self):
        self.phase_req_1 = self.get_nym()
        self.phase_req_2 = self.get_nym()
        self.phase_req_3 = self.get_nym()

        self.default_auth_rule = self.get_default_auth_rule()
        self.changed_auth_rule = self.get_changed_auth_rule()


    def run(self):
        # Step 1. Check default auth rule
        self.send_and_check(self.phase_req_1)

        # Step 2. Change auth rule
        self.send_and_check(self.changed_auth_rule)

        # Step 3. Check, that we cannot add new steward by old way
        with pytest.raises(RequestRejectedException):
            self.send_and_check(self.phase_req_2)

        # Step 4. Return default auth rule
        self.send_and_check(self.default_auth_rule)

        # Step 5. Check, that default auth rule works
        self.send_and_check(self.phase_req_3)

    def result(self):
        pass


    def send_and_check(self, req):
        signed_reqs = sdk_multi_sign_request_objects(self.looper,
                                                     [self.creator_wallet],
                                                     [req])
        request_couple = sdk_send_signed_requests(self.sdk_pool_handle,
                                                  signed_reqs)[0]

        return sdk_get_and_check_replies(self.looper,
                                         [request_couple])[0]

    def get_nym(self):
        wh, _ = self.creator_wallet
        did, _ = create_verkey_did(self.looper, wh)
        return self._build_nym(self.creator_wallet, self.role_string, did)

    def get_changed_auth_rule(self):
        constraint = AuthConstraint(role=TRUST_ANCHOR,
                                    sig_count=1,
                                    need_to_be_owner=False)
        operation = generate_auth_rule_operation(auth_action=ADD_PREFIX,
                                                 auth_type=NYM,
                                                 field=ROLE,
                                                 new_value=self.role,
                                                 constraint=constraint.as_dict)
        return sdk_gen_request(operation, identifier=self.creator_wallet[1])


class AddNewTrusteeTest(AddNewRoleTest):
    def __init__(self, env):
        super().__init__(auth_map.add_new_trustee.get_action_id(), env.sdk_wallet_trustee, env)


class AddNewStewardTest(AddNewRoleTest):
    def __init__(self, env):
        super().__init__(auth_map.add_new_steward.get_action_id(), env.sdk_wallet_trustee, env)


class AddNewTrustAnchorTest(AddNewRoleTest):
    def __init__(self, env):
        super().__init__(auth_map.add_new_trust_anchor.get_action_id(), env.sdk_wallet_trustee, env)


class AddNewNetworkMonitorTest(AddNewRoleTest):
    def __init__(self, env):
        super().__init__(auth_map.add_new_network_monitor.get_action_id(), env.sdk_wallet_trustee, env)


class AddNewIdentityOwnerTest(AddNewRoleTest):
    def __init__(self, env):
        super().__init__(auth_map.add_new_identity_owner.get_action_id(), env.sdk_wallet_trustee, env)