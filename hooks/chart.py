"""Chart generation hook that adds matplotlib charts to responses."""

import random
import base64
import io
from typing import Dict, Any

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt


def chart_hook(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a matplotlib chart and add it to the response as an image.
    
    This hook creates a sample chart with fake data and embeds it as a base64-encoded
    image in the OpenAI-compatible response format.
    
    Args:
        response: The OpenAI response dictionary
        
    Returns:
        Modified response dictionary with chart image added
    """
    if "choices" not in response or len(response["choices"]) == 0:
        return response
    
    choice = response["choices"][0]
    if "message" not in choice:
        return response
    
    message = choice["message"]
    
    # Generate fake data for the chart
    categories = ['Q1', 'Q2', 'Q3', 'Q4']
    values = [random.randint(50, 100) for _ in categories]
    
    # Create the chart
    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(categories, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'])
    ax.set_ylabel('Sales (thousands)', fontsize=12)
    ax.set_xlabel('Quarter', fontsize=12)
    ax.set_title('Quarterly Sales Performance', fontsize=14, fontweight='bold')
    ax.set_ylim(0, max(values) * 1.2)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    
    # Convert chart to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)  # Close the figure to free memory
    
    # Get the original text content
    original_content = message.get("content", "")
    
    # Convert message content to array format with text and image
    content_array = [
        {
            "type": "text",
            "text": original_content
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{image_base64}"
            }
        }
    ]
    
    # Update the message content
    message["content"] = content_array
    
    return response

