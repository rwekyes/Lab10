import asyncio
import shelve
from bleak import BleakScanner as bs
from time import strftime, gmtime, sleep

async def scan_for_devices():
    print("Scanning for Bluetooth Devices....")
    devices = await bs.discover()
    for device in devices:
        print(f"Device Name: {device.name}, Device Address: {device.address}")
    return devices

KNOWN_DEVICES = {
    "[TV] Living room": "40:16:3B:4F:CA:97",
    "None": "34:DC:40:5E:5F:9E"
}

async def check_for_known_devices():
    devices = await bs.discover()
    nearby_known_devices = {}

    for device in devices:
        if device.address in KNOWN_DEVICES.values():
            device_name = [name for name, addr in KNOWN_DEVICES.items() if addr == device.address][0]
            print(f"{device_name} is nearby!")
            nearby_known_devices[device_name] = device.address

    return nearby_known_devices

def log_devices(devices):
    with shelve.open( "device_log" ) as db:
        for name, address in devices.items():
            key = name + '_' + address
            formatted_time = strftime( "%Y-%m-%d %H:%M:%S", gmtime())
            if key in db:
                time_list = db[key]
                time_list.append(formatted_time)
                db[key] = time_list
            else:
                db[key] = [formatted_time]
    print( "Logged devices in the shelf database." )

async def scan():
    nearby_devices = await check_for_known_devices()
    if nearby_devices:
        log_devices(nearby_devices)
    else:
        print("No known devices nearby.")

async def clear_logs_every_hour():
    while True:
        await asyncio.sleep(3600)
        with shelve.open("device_log") as db:
            db.clear()
        print(f"Cleared the device log")

async def scan_loop():
    while True:
        print("Scanning...")
        await scan()
        print("Sleeping till next loop...")
        await asyncio.sleep(15)
        print("Verifying log...")
        with shelve.open("device_log") as db:
            for name, times in db.items():
                print(f"{name}: {times}")


# Spiffed it up a bit:

async def wait_for_quit():
    while True:
        key = await asyncio.to_thread(
            input)  # input() runs in a thread, so scanning continues
        if key.strip().lower() == "q":
            return


async def main():
    print("Press q then Enter to quit.")
    tasks = [
        asyncio.create_task(scan_loop()),
        asyncio.create_task(clear_logs_every_hour()),
    ]
    await wait_for_quit()  # blocks here until the user quits
    for t in tasks:
        t.cancel()  # stop both loops
    await asyncio.gather(*tasks,
                         return_exceptions=True)  # let them finish cancelling
    print("Goodbye!")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:  # Ctrl+C still works as a backup
        print("\nInterrupted, exiting.")