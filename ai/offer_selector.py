def select_offer(analysis):

    a = analysis.lower()

    if "ecommerce" in a:
        return "feedback"
    elif "saas" in a:
        return "chatbot"
    elif "agency" in a:
        return "dashboard"
    elif "law" in a:
        return "chatbot"
    elif "logistics" in a:
        return "dashboard"

    return "dashboard"