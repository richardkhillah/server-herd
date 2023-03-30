from time import time, strftime, sleep

import asyncio
import json
import sys

ipaddr = '127.0.0.1'

my_herd = {
    'Bailey': 17800,
    'Bona': 17801,
    'Campbell': 17802,
    'Clark': 17803,
    'Jaquez': 17804,
}
seas_herd = {
    'Bailey': 10000,
    'Bona': 10001,
    'Campbell': 10002,
    'Clark': 10003,
    'Jaquez': 10004,
}
herd = my_herd

def iamat(host, coord, t=None, skew=None):
    if t is None:
        t = time()
    if skew is not None:
        t + skew
        print(f'{(t+skew)=}')
    formatted = f"IAMAT {host} {coord} {t}"
    return formatted

def whatsat(host, radius, page):
    formatted = f"WHATISAT {host} {radius} {page}"
    return formatted

def invalid_command(command):
    return f'{command}'

async def tcp_echo_client(message, server):
    reader, writer = await asyncio.open_connection(
        ipaddr, herd[server])

    print(f'Send to {server}: {message}')
    writer.write(message.encode())
    await writer.drain()
    writer.write_eof()

    data = await reader.read()
    decoded_data = data.decode()

    # split_message = message.split()
    # split_data = decoded_data.split()
    
    print(f'Received: {decoded_data}')


    print('Close the connection')
    writer.close()
    await writer.wait_closed()

async def time_after(n):
    print(f'sleep for {n=}')
    await asyncio.sleep(n)
    print(f'wokeup')
    return time()

async def main():
    addrs = ['kiwi.cs.ucla.edu', 'plum.cs.ucla.edu', 'watermelon.cs.ucla.edu']
    hosts = {k.split('.')[0]: k for k in addrs}
    coordinates = {
        'ucla': '+34.069072065913495-118.44518110210453',
        'alcatraz': '+37.827160394635804-122.4229566155028',
        'gordon': '+42.8066597474685-102.20244258652899',
        'dc': '+38.89787667717704 -77.03651907314573',
        'wounded': '+43.14272554411939-102.36505934705043',
        'minneapolis': '+44.9481292661016-93.27610373604308',
        'test': '+34.068930-118.445127',
    }
    # coordinates = ['+34.068930-118.445127', '+55.555555-666.666666', '+77.777777-888.888888']
    # times = await asyncio.gather(
    #     *(time_after(i) for i in range(6)))

    try:
        await tcp_echo_client('WHATSAT kiwi.cs.ucla.edu 10 5', 'Clark')
        await time_after(5)
        await tcp_echo_client('IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1621464827.959498503', 'Bailey')
        await tcp_echo_client('WHATSAT kiwi.cs.ucla.edu 10 5', 'Clark')


        # Single Server Tests
        # Test invalid command
        # print('\n==================================================')
        # print('Testing Single-Server Invalid Command to Bailey')
        # await tcp_echo_client(invalid_command('DUMMY'), 'Bailey')

        # # Test iamat format:
        # # Invalid IAMAT
        # print('\n==================================================')
        # print('Testing Single-Server Invalid IAMAT format to Bailey')
        # await tcp_echo_client(iamat(' ', coordinates['test']), 'Bailey')
        # await tcp_echo_client(iamat(hosts['kiwi'], 'notcorrect'), 'Bailey')
        # await tcp_echo_client(iamat('another bad', 'notcorrect'), 'Bailey')

        # # VALID IAMAT
        # print('\n==================================================')
        # print('Testing Single-Server Valid IAMAT format to Bailey')
        # await tcp_echo_client(iamat(hosts['kiwi'], coordinates['test']), 'Bailey')

        # # Test whatisat format:
        # # Invalid WHATISAT
        # print('\n==================================================')
        # print('Testing Single-Server Invalid WHATISAT format to Bailey')
        # await tcp_echo_client(whatsat('Invalid address', 1, 1), 'Bailey') # Invalid address format
        # await tcp_echo_client(whatsat(hosts['plum'], 1, 1), 'Bailey') # Unkonwn address
        # await tcp_echo_client(whatsat(hosts['kiwi'], -1, 1), 'Bailey') # Invalid Radius
        # await tcp_echo_client(whatsat(hosts['kiwi'], 51, 1), 'Bailey') # Invalid Radius
        # await tcp_echo_client(whatsat(hosts['kiwi'], 1, -1), 'Bailey') # Invalid result size
        # await tcp_echo_client(whatsat(hosts['kiwi'], 1, 21), 'Bailey') # Invalid result size

        # # VALID WHATISAT
        # print('\n==================================================')
        # print('Testing Single-Server Valid WHATISAT format to Bailey')
        # await tcp_echo_client(whatsat(hosts['kiwi'], 1, 1), 'Bailey')

        # # Multi Server Tests
        # # Direct communcation
        # print('\n==================================================')
        # print('Multi-Server- Testing')
        # print('==================================================')
        # print('Testing Multi-server Communication Direct Communication from Bailey')
        # await tcp_echo_client(whatsat(hosts['kiwi'], 1, 1), 'Bona') # Bailey talks with Bona
        # await tcp_echo_client(whatsat(hosts['kiwi'], 1, 1), 'Campbell') # Bailey talks with Campbell

        # # Indirect communication
        # print('\n==================================================')
        # print('Testing Multi-server Communication Indirect Communication from Bailey')
        # await tcp_echo_client(whatsat(hosts['kiwi'], 1, 1), 'Clark') # Bona and Campbell talks with Clark
        # await tcp_echo_client(whatsat(hosts['kiwi'], 1, 1), 'Jaquez') # Clark and Campbell talk with Jaquez











        # await tcp_echo_client(whatsat(hosts['kiwi'], 1, 1), 'Bailey')
        # await asyncio.sleep(1)
        # await tcp_echo_client(whatsat(hosts['kiwi'], 1, 1), 'Bona')
        # await tcp_echo_client(iamat(hosts['kiwi'], coordinates['alcatraz']), 'Bona')

        
        # await tcp_echo_client(iamat(hosts['kiwi'], coordinates['ucla']), 'Clark')
        # await time_after(1)
        # await tcp_echo_client(whatsat(hosts['kiwi'], 1, 2), 'Jaquez')

        # await tcp_echo_client(iamat(hosts['kiwi'], coordinates['ucla']), 'Bailey')
        # await time_after(2)
        # await tcp_echo_client(whatsat(hosts['kiwi'], 1, 2), 'Clark')

        # await time_after(5)

        # await asyncio.gather(
        #     tcp_echo_client(iamat(hosts['kiwi'], coordinates['gordon']), 'Jaquez'),
        #     tcp_echo_client(whatsat(hosts['kiwi'], 2, 2), 'Bailey'),
        # )
        
        # await time_after(5)

        # await asyncio.gather(
        #     tcp_echo_client(whatsat(hosts['watermelon'], 2, 2), 'Bailey'),
        #     tcp_echo_client(whatsat(hosts['watermelon'], 2, 2), 'Bona'),
        #     tcp_echo_client(whatsat(hosts['watermelon'], 2, 2), 'Campbell'),
        #     tcp_echo_client(whatsat(hosts['watermelon'], 2, 2), 'Clark'),
        #     tcp_echo_client(whatsat(hosts['watermelon'], 2, 2), 'Jaquez'),
        #     tcp_echo_client(iamat(hosts['watermelon'], coordinates['dc']), 'Clark'),
        #     tcp_echo_client(whatsat(hosts['watermelon'], 2, 2), 'Bailey'),
        # )

    except ConnectionRefusedError as cre:
        print("Connection Refused")
        print(cre)
        sys.exit(-1)

if __name__ == '__main__':
    asyncio.run(main())