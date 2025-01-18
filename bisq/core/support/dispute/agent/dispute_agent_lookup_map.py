from bisq.core.locale.res import Res
import re
import logging

log = logging.getLogger(__name__)


class DisputeAgentLookupMap:

    # See also: https://bisq.wiki/Finding_your_mediator
    @staticmethod
    def get_matrix_user_name(full_address):
        if re.match(r"localhost(.*)", full_address):
            return full_address  # on regtest, agent displays as localhost

        if full_address in [
            "saavbszijyrqrj4opgiirusnrpv6ntabttuzvjaqmx7j4r7mlz5eibqd.onion:9999",
            "7hkpotiyaukuzcfy6faihjaols5r2mkysz7bm3wrhhbpbphzz3zbwyqd.onion:9999"   # old
        ]:
            return "leo816"
        elif full_address == "3z5jnirlccgxzoxc6zwkcgwj66bugvqplzf6z2iyd5oxifiaorhnanqd.onion:9999":
            return "refundagent2"
        elif full_address == "aguejpkhhl67nbtifvekfjvlcyagudi6d2apalcwxw7fl5n7qm2ll5id.onion:9999":
            return "luis3672"
        elif full_address in [
            "d7m3j3u4jo2yuymgvxisklpitd3n5xbsnnpyz2mjh6bl6gmj5rjdxead.onion:9999",
            "6c4cim7h7t3bm4bnchbf727qrhdfrfr6lhod25wjtizm2sifpkktvwad.onion:9999"   # old
        ]:
            return "pazza83"
        else:
            log.warning(
            f"No user name for dispute agent with address {full_address} found."
            )
            return Res.get("shared.na")

    @staticmethod
    def get_matrix_link_for_agent(onion):
        # when a new mediator starts or an onion address changes, mediator name won't be known until
        # the table above is updated in the software.
        # as a stopgap measure, replace unknown ones with a link to the Bisq team
        agent_name = DisputeAgentLookupMap.get_matrix_user_name(onion).replace(
            Res.get("shared.na"), "bisq"
        )
        return f"https://matrix.to/#/@{agent_name}:matrix.org"
