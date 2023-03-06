import socket

from . import defaults as defs


def cleanup_ip(ip):
    """
    Given ip address string, it cleans it up
    """
    clean_ip = None
    ip = ip.strip()
    try:
        # Try v4
        clean_ip = socket.inet_ntop(socket.AF_INET, socket.inet_pton(socket.AF_INET, ip))
    except AttributeError:  # pragma: no cover
        try:  # Fall-back on legacy API
            # Note that inet_ntoa will convert 127.1 whereas inet_pton will not.
            clean_ip = socket.inet_ntoa(socket.inet_aton(ip))
        except AttributeError:
            pass
    except socket.error:
        pass

    if not clean_ip:
        try:
            # Try v6
            clean_ip = socket.inet_ntop(socket.AF_INET6, socket.inet_pton(socket.AF_INET6, ip))
            if clean_ip.startswith('::ffff:'):
                return clean_ip.replace('::ffff:', '')

        except socket.error:
            pass

    return clean_ip or ip


def is_valid_ipv4(ip_str):
    """
    Check the validity of an IPv4 address
    """
    try:
        socket.inet_pton(socket.AF_INET, ip_str)
    except AttributeError:  # pragma: no cover
        try:  # Fall-back on legacy API or False
            socket.inet_aton(ip_str)
        except (AttributeError, socket.error):
            return False
        return ip_str.count('.') == 3
    except socket.error:
        return False
    return True


def is_valid_ipv6(ip_str):
    """
    Check the validity of an IPv6 address
    """
    try:
        socket.inet_pton(socket.AF_INET6, ip_str)
    except socket.error:
        return False
    return True


def is_valid_ip(ip_str):
    """
    Check the validity of an IP address
    """
    return is_valid_ipv4(ip_str) or is_valid_ipv6(ip_str)


def is_private_ip(ip_str):
    """
    Returns true of ip_str is private & not routable, else return false
    """
    return ip_str.startswith(defs.IPWARE_NON_PUBLIC_IP_PREFIX)


def is_public_ip(ip_str):
    """
    Returns true of ip_str is public & routable, else return false
    """
    return not is_private_ip(ip_str)


def is_loopback_ip(ip_str):
    """
    Returns true of ip_str is public & routable, else return false
    """
    return ip_str.startswith(defs.IPWARE_LOOPBACK_PREFIX)


def get_request_meta(request, key):
    """
    Given a key, it returns a cleaned up version of the value from request.META, or None
    """
    value = request.META.get(key, request.META.get(key.replace('_', '-'), '')).strip()
    if value == '':
        return None
    return value


def get_ips_from_string(ip_str):
    """
    Given a string, it returns a list of one or more valid IP addresses
    """
    ip_list = []

    for ip in ip_str.split(','):
        clean_ip = ip.strip().lower()
        if clean_ip:
            ip_list.append(clean_ip)

    ip_count = len(ip_list)
    if ip_count > 0 and is_valid_ip(ip_list[0]) and is_valid_ip(ip_list[-1]):
        return ip_list, ip_count

    return [], 0


def get_ip_info(ip_str):
    """
    Given a string, it returns a tuple of (IP, Routable).
    """
    ip = None
    is_routable_ip = False
    clean_ip = cleanup_ip(ip_str)
    if is_valid_ip(clean_ip):
        ip = clean_ip
        is_routable_ip = is_public_ip(ip)
    return ip, is_routable_ip


def get_best_ip(last_ip, next_ip):
    """
    Given two IP addresses, it returns the the best match ip.
    Order of precedence is (Public, Private, Loopback, None)
    Right-most IP is returned
    """
    if last_ip is None:
        return next_ip
    clean_last_ip = cleanup_ip(last_ip)
    clean_next_ip = cleanup_ip(next_ip)
    if is_public_ip(clean_last_ip) and not is_public_ip(clean_next_ip):
        return last_ip
    if is_private_ip(clean_last_ip) and is_loopback_ip(clean_next_ip):
        return last_ip
    return next_ip
