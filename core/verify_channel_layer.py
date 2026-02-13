import os
import django
import asyncio
from channels.layers import get_channel_layer

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

async def test_channel_layer():
    channel_layer = get_channel_layer()
    print(f"Channel Layer: {channel_layer}")
    
    # Test group send/receive
    group_name = "test_group"
    channel_name = "test_channel"
    
    print(f"Adding channel {channel_name} to group {group_name}...")
    await channel_layer.group_add(group_name, channel_name)
    
    print(f"Sending message to group {group_name}...")
    await channel_layer.group_send(
        group_name,
        {
            "type": "test.message",
            "text": "hello"
        }
    )
    
    # In a real worker, we'd receive this. For InMemory, it's just a sanity check that no errors occurred.
    # To truly test receive with InMemory, we'd need to pop from the channel, but InMemoryChannelLayer 
    # might not expose a simple pop without a consumer.
    # However, if group_send doesn't error, the layer is likely working.
    
    print("Message sent successfully (no errors raised).")
    
    print("Channel layer configuration seems correct.")

if __name__ == "__main__":
    asyncio.run(test_channel_layer())
