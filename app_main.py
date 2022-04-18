from app_token import AppToken
import argparse

# Color
_RED = '\x01'
_GREEN = '\x02'
_NONE = '\x00'


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-r', '--read', action="store_true", help="read token")
    group.add_argument('-w', '--write', action="store_true", help="write token")
    group.add_argument('-i', '--info', action="store_true", help="reader information")
    parser.add_argument('-s', '--serial', action="store_true", help="view serial communication device")
    parser.add_argument('-v', '--verbose', action="store_true", help="trace serial commands")
    parser.add_argument('-d', '--data', help="(write only) data", default=None)
    args = parser.parse_args()

    if args.verbose:
        token = AppToken('/dev/ttyUSB0', debug=True)
    else:
        token = AppToken('/dev/ttyUSB0')

    if args.serial:
        token.list_port()

    if args.info:
        print(token.get_info().decode())

    elif args.read:
        _token = token.read_token()
        if _token is None:
            print("No card present")
        else:
            print(f'Default token - {_token}')

    elif args.write:
        if args.data is not None:
            status = token.write_token(args.data)
            if status == 0:
                print(f'Write token {args.data} successfully.')
        else:
            parser.print_help()
            exit(1)
    if not any(args.__dict__.values()):
        parser.print_help()
        exit(1)
