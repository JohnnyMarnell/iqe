"""Create 60 ArtNet universes for 420x24 pixel output"""

print("Creating 60 universe splitters...")
video_to_dmx = op('/project1/video_to_dmx')
dmx_outputs = []

# TouchDesigner class types
from td import selectCHOP, dmxoutCHOP

for universe_id in range(60):
    # Create select CHOP for this universe's channels
    select_chop = op('/project1').create(selectCHOP, f'universe_{universe_id}_select')
    
    # Calculate channel range for this universe
    start_chan = universe_id * 512
    end_chan = min(start_chan + 511, 30239)
    
    # Set channel selection by index range
    select_chop.par.channames = f'{start_chan}-{end_chan}'
    select_chop.par.renameto = 'chan[0-511]'
    
    # Connect video_to_dmx to select
    video_to_dmx.outputConnectors[0].connect(select_chop)
    
    # Create DMX Out for this specific universe
    dmx_out = op('/project1').create(dmxoutCHOP, f'artnet_universe_{universe_id}')
    dmx_out.par.interface = 'artnet'
    dmx_out.par.subnet = 0
    dmx_out.par.universe = universe_id
    dmx_out.par.multicast = True
    dmx_out.par.netaddress = '192.168.1.255'
    dmx_out.par.active = True
    
    # Connect select to DMX out
    select_chop.outputConnectors[0].connect(dmx_out)
    
    # Position nodes in grid
    row = universe_id // 10
    col = universe_id % 10
    
    select_chop.nodeX = col * 200 - 1000
    select_chop.nodeY = -200 - (row * 100)
    
    dmx_out.nodeX = col * 200 - 1000
    dmx_out.nodeY = -300 - (row * 100)
    
    dmx_outputs.append((select_chop, dmx_out))
    
    if universe_id % 10 == 0:
        print(f"Created universes {universe_id} - {min(universe_id + 9, 59)}")

print(f"Created {len(dmx_outputs)} universe outputs")

# Position video_to_dmx node at top
video_to_dmx.nodeX = 0
video_to_dmx.nodeY = 100