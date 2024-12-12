from bisq.core.util.validation.regex_validator import RegexValidator


class RegexValidatorFactory:
    @staticmethod
    def address_regex_validator():
        regex_validator = RegexValidator()
        port_regex_pattern = r"(0|[1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])"
        onion_v2_regex_pattern = fr"[a-zA-Z2-7]{{16}}\.onion(?:\:{port_regex_pattern})?"
        onion_v3_regex_pattern = fr"[a-zA-Z2-7]{{56}}\.onion(?:\:{port_regex_pattern})?"
        ipv4_regex_pattern = r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}" + \
                            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)" + \
                            fr"(?:\:{port_regex_pattern})?"
        ipv6_regex_pattern = (r"(" + 
                r"([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|" +              # 1:2:3:4:5:6:7:8
                r"([0-9a-fA-F]{1,4}:){1,7}:|" +                             # 1::                              1:2:3:4:5:6:7::
                r"([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|" +             # 1::8             1:2:3:4:5:6::8  1:2:3:4:5:6::8
                r"([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|" +      # 1::7:8           1:2:3:4:5::7:8  1:2:3:4:5::8
                r"([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|" +      # 1::6:7:8         1:2:3:4::6:7:8  1:2:3:4::8
                r"([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|" +      # 1::5:6:7:8       1:2:3::5:6:7:8  1:2:3::8
                r"([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|" +      # 1::4:5:6:7:8     1:2::4:5:6:7:8  1:2::8
                r"[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|" +           # 1::3:4:5:6:7:8   1::3:4:5:6:7:8  1::8
                r":((:[0-9a-fA-F]{1,4}){1,7}|:)|" +                         # ::2:3:4:5:6:7:8  ::2:3:4:5:6:7:8 ::8       ::
                r"fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|" +         # fe80::7:8%eth0   fe80::7:8%1
                r"::(ffff(:0{1,4}){0,1}:){0,1}" +                           # (link-local IPv6 addresses with zone index)
                r"((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}" +
                r"(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|" +              # ::255.255.255.255   ::ffff:255.255.255.255  ::ffff:0:255.255.255.255
                r"([0-9a-fA-F]{1,4}:){1,4}:" +                              # (IPv4-mapped IPv6 addresses and IPv4-translated addresses)
                r"((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}" + 
                r"(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])" +               # 2001:db8:3:4::192.0.2.33  64:ff9b::192.0.2.33
                r")"                                                        # (IPv4-Embedded IPv6 Address)
            )                                                       
        ipv6_regex_pattern = fr"(?:{ipv6_regex_pattern})|(?:\[{ipv6_regex_pattern}\]\:{port_regex_pattern})"
        fqdn_regex_pattern = fr"(((?!-)[a-zA-Z0-9-]{{1,63}}(?<!-)\.)+(?!onion)[a-zA-Z]{{2,63}}(?:\:{port_regex_pattern})?)"
        
        final_pattern = fr"^(?:(?:(?:{onion_v2_regex_pattern})|(?:{onion_v3_regex_pattern})|(?:{ipv4_regex_pattern})|(?:{ipv6_regex_pattern})|(?:{fqdn_regex_pattern})),\s*)*(?:(?:{onion_v2_regex_pattern})|(?:{onion_v3_regex_pattern})|(?:{ipv4_regex_pattern})|(?:{ipv6_regex_pattern})|(?:{fqdn_regex_pattern}))*$"
        
        regex_validator.pattern = final_pattern
        return regex_validator

    @staticmethod
    def onion_address_regex_validator():
        """checks if valid tor onion hostname with optional port at the end"""
        regex_validator = RegexValidator()
        port_regex_pattern = r"(0|[1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])"
        onion_v2_regex_pattern = fr"[a-zA-Z2-7]{{16}}\.onion(?:\:{port_regex_pattern})?"
        onion_v3_regex_pattern = fr"[a-zA-Z2-7]{{56}}\.onion(?:\:{port_regex_pattern})?"
        
        regex_validator.pattern = fr"^(?:(?:(?:{onion_v2_regex_pattern})|(?:{onion_v3_regex_pattern})),\s*)*(?:(?:{onion_v2_regex_pattern})|(?:{onion_v3_regex_pattern}))*$"
        return regex_validator

    @staticmethod
    def localhost_address_regex_validator():
        """checks if localhost address, with optional port at the end"""
        regex_validator = RegexValidator()
        
        # match 0 ~ 65535
        port_regex_pattern = r"(0|[1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])"
        
        # match 127/8 (127.0.0.0 ~ 127.255.255.255)
        localhost_ipv4_regex_pattern = fr"(?:127\.)" + \
            r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){2}" + \
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)" + \
            fr"(?:\:{port_regex_pattern})?"
        
        # match ::/64 with optional port at the end, i.e. ::1 or [::1]:8081
        localhost_ipv6_regex_pattern = r"(:((:[0-9a-fA-F]{1,4}){1,4}|:)|)"
        localhost_ipv6_regex_pattern = fr"(?:{localhost_ipv6_regex_pattern})|(?:\[{localhost_ipv6_regex_pattern}\]\:{port_regex_pattern})"
        
        # match *.local
        localhost_fqdn_regex_pattern = fr"(localhost(?:\:{port_regex_pattern})?)"
        
        regex_validator.pattern = fr"^(?:(?:(?:{localhost_ipv4_regex_pattern})|(?:{localhost_ipv6_regex_pattern})|(?:{localhost_fqdn_regex_pattern})),\s*)*(?:(?:{localhost_ipv4_regex_pattern})|(?:{localhost_ipv6_regex_pattern})|(?:{localhost_fqdn_regex_pattern}))*$"
        return regex_validator

    @staticmethod
    def localnet_address_regex_validator():
        """checks if local area network address, with optional port at the end"""
        regex_validator = RegexValidator()
        
        # match 0 ~ 65535
        port_regex_pattern = r"(0|[1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])"
        
        # match 10/8 (10.0.0.0 ~ 10.255.255.255)
        localnet_ipv4_pattern_a = fr"(?:10\.)" + \
            r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){2}" + \
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)" + \
            fr"(?:\:{port_regex_pattern})?"
            
        # match 172.16/12 (172.16.0.0 ~ 172.31.255.255)
        localnet_ipv4_pattern_b = fr"(?:172\.)" + \
            r"(?:(?:1[6-9]|2[0-9]|[3][0-1])\.)" + \
            r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.)" + \
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)" + \
            fr"(?:\:{port_regex_pattern})?"

        # match 192.168/16 (192.168.0.0 ~ 192.168.255.255)
        localnet_ipv4_pattern_c = fr"(?:192\.)" + \
            r"(?:168\.)" + \
            r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.)" + \
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)" + \
            fr"(?:\:{port_regex_pattern})?"

        # match 169.254/15 (169.254.0.0 ~ 169.255.255.255)
        autolocal_ipv4_pattern = fr"(?:169\.)" + \
            r"(?:(?:254|255)\.)" + \
            r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.)" + \
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)" + \
            fr"(?:\:{port_regex_pattern})?"

        # match fc00::/7 (fc00:: ~ fdff:ffff:ffff:ffff:ffff:ffff:ffff:ffff)
        localnet_ipv6_pattern = (r"(" +
            r"([fF][cCdD][0-9a-fA-F]{2}:)([0-9a-fA-F]{1,4}:){6}[0-9a-fA-F]{1,4}|" +             # fd00:2:3:4:5:6:7:8
            r"([fF][cCdD][0-9a-fA-F]{2}:)([0-9a-fA-F]{1,4}:){0,7}:|" +                          # fd00::                                 fd00:2:3:4:5:6:7::
            r"([fF][cCdD][0-9a-fA-F]{2}:)([0-9a-fA-F]{1,4}:){0,6}:[0-9a-fA-F]{1,4}|" +          # fd00::8             fd00:2:3:4:5:6::8  fd00:2:3:4:5:6::8
            r"([fF][cCdD][0-9a-fA-F]{2}:)([0-9a-fA-F]{1,4}:){0,5}(:[0-9a-fA-F]{1,4}){1,1}|" +   # fd00::7:8           fd00:2:3:4:5::7:8  fd00:2:3:4:5::8
            r"([fF][cCdD][0-9a-fA-F]{2}:)([0-9a-fA-F]{1,4}:){0,4}(:[0-9a-fA-F]{1,4}){1,2}|" +   # fd00::7:8           fd00:2:3:4:5::7:8  fd00:2:3:4:5::8
            r"([fF][cCdD][0-9a-fA-F]{2}:)([0-9a-fA-F]{1,4}:){0,3}(:[0-9a-fA-F]{1,4}){1,3}|" +   # fd00::6:7:8         fd00:2:3:4::6:7:8  fd00:2:3:4::8
            r"([fF][cCdD][0-9a-fA-F]{2}:)([0-9a-fA-F]{1,4}:){0,2}(:[0-9a-fA-F]{1,4}){1,4}|" +   # fd00::5:6:7:8       fd00:2:3::5:6:7:8  fd00:2:3::8
            r"([fF][cCdD][0-9a-fA-F]{2}:)([0-9a-fA-F]{1,4}:){0,1}(:[0-9a-fA-F]{1,4}){1,5}|" +   # fd00::4:5:6:7:8     fd00:2::4:5:6:7:8  fd00:2::8
            r"([fF][cCdD][0-9a-fA-F]{2}:)(:[0-9a-fA-F]{1,4}){1,6}" +                            # fd00::3:4:5:6:7:8   fd00::3:4:5:6:7:8  fd00::8
            r")")

        # match fe80::/10 (fe80:: ~ febf:ffff:ffff:ffff:ffff:ffff:ffff:ffff)
        autolocal_ipv6_pattern = (r"(" +
            r"([fF][eE][8-9a-bA-B][0-9a-fA-F]:)([0-9a-fA-F]{1,4}:){6}[0-9a-fA-F]{1,4}|" +            # fe80:2:3:4:5:6:7:8
            r"([fF][eE][8-9a-bA-B][0-9a-fA-F]:)([0-9a-fA-F]{1,4}:){0,7}:|" +                         # fe80::                                 fe80:2:3:4:5:6:7::
            r"([fF][eE][8-9a-bA-B][0-9a-fA-F]:)([0-9a-fA-F]{1,4}:){0,6}:[0-9a-fA-F]{1,4}|" +         # fe80::8             fe80:2:3:4:5:6::8  fe80:2:3:4:5:6::8
            r"([fF][eE][8-9a-bA-B][0-9a-fA-F]:)([0-9a-fA-F]{1,4}:){0,5}(:[0-9a-fA-F]{1,4}){1,1}|" +  # fe80::7:8           fe80:2:3:4:5::7:8  fe80:2:3:4:5::8
            r"([fF][eE][8-9a-bA-B][0-9a-fA-F]:)([0-9a-fA-F]{1,4}:){0,4}(:[0-9a-fA-F]{1,4}){1,2}|" +  # fe80::7:8           fe80:2:3:4:5::7:8  fe80:2:3:4:5::8
            r"([fF][eE][8-9a-bA-B][0-9a-fA-F]:)([0-9a-fA-F]{1,4}:){0,3}(:[0-9a-fA-F]{1,4}){1,3}|" +  # fe80::6:7:8         fe80:2:3:4::6:7:8  fe80:2:3:4::8
            r"([fF][eE][8-9a-bA-B][0-9a-fA-F]:)([0-9a-fA-F]{1,4}:){0,2}(:[0-9a-fA-F]{1,4}){1,4}|" +  # fe80::5:6:7:8       fe80:2:3::5:6:7:8  fe80:2:3::8
            r"([fF][eE][8-9a-bA-B][0-9a-fA-F]:)([0-9a-fA-F]{1,4}:){0,1}(:[0-9a-fA-F]{1,4}){1,5}|" +  # fe80::4:5:6:7:8     fe80:2::4:5:6:7:8  fe80:2::8
            r"([fF][eE][8-9a-bA-B][0-9a-fA-F]:)(:[0-9a-fA-F]{1,4}){1,6}" +                           # fe80::3:4:5:6:7:8   fe80::3:4:5:6:7:8  fe80::8
            r")")

        # allow for brackets with optional port at the end
        localnet_ipv6_pattern = fr"(?:{localnet_ipv6_pattern})|(?:\[{localnet_ipv6_pattern}\]\:{port_regex_pattern})"
        autolocal_ipv6_pattern = fr"(?:{autolocal_ipv6_pattern})|(?:\[{autolocal_ipv6_pattern}\]\:{port_regex_pattern})"

        # match *.local
        local_fqdn_pattern = fr"(((?!-)[a-zA-Z0-9-]{{1,63}}(?<!-)\.)+local(?:\:{port_regex_pattern})?)"

        regex_validator.pattern = fr"^(?:(?:(?:{localnet_ipv4_pattern_a})|(?:{localnet_ipv4_pattern_b})|(?:{localnet_ipv4_pattern_c})|(?:{autolocal_ipv4_pattern})|(?:{localnet_ipv6_pattern})|(?:{autolocal_ipv6_pattern})|(?:{local_fqdn_pattern})),\s*)*(?:(?:{localnet_ipv4_pattern_a})|(?:{localnet_ipv4_pattern_b})|(?:{localnet_ipv4_pattern_c})|(?:{autolocal_ipv4_pattern})|(?:{localnet_ipv6_pattern})|(?:{autolocal_ipv6_pattern})|(?:{local_fqdn_pattern}))*$"
        return regex_validator

