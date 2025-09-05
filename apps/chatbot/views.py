# apps/chatbot/views.py
import os
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate

from apps.orders.models import Order

# Create a dict in memory (not persisted)
SESSION_MEMORIES = {}

def get_chat_memory(session_key):
    if session_key not in SESSION_MEMORIES:
        SESSION_MEMORIES[session_key] = ConversationBufferMemory(return_messages=True)
    return SESSION_MEMORIES[session_key]

@login_required
def chat_page(request):
    """Render the chatbot page (floating widget UI)."""
    return render(request, "chatbot/chat.html")

@login_required
def chat_api(request):
    """AJAX endpoint for sending/receiving chat messages."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    user = request.user
    user_msg = request.POST.get("message", "").strip()
    if not user_msg:
        return JsonResponse({"error": "Empty message"}, status=400)

    # fetch memory for this user’s session
    memory = get_chat_memory(request.session.session_key)

    # ADMIN CONTEXT
    if user.is_superuser or user.email == "t.shakthi@gmail.com":
        qs = Order.objects.all()
        total = qs.count()
        cancelled = qs.filter(status=Order.STATUS_CANCELLED).count()
        refunded = qs.filter(status=Order.STATUS_REFUNDED).count()
        inprogress = qs.filter(status=Order.STATUS_IN_PROGRESS).count()
        delivered = qs.filter(status=Order.STATUS_DELIVERED).count()

        context = f"""
        You are Taylor, a helpful assistant for the **admin**.

        The logged-in admin is: {user.get_full_name() or user.username} (email: {user.email}).

        Rules:
        - The admin can see aggregated statistics of all orders.
        - Do not allow deletion or insertion of books/orders from this chat.
        - Politely refuse if asked to modify database records.
        - You may summarize counts, totals, or high-level stats.

        Current stats:
        Total Orders: {total}, In Progress: {inprogress}, Delivered: {delivered},
        Cancelled: {cancelled}, Refunded: {refunded}.
        """

    # CUSTOMER CONTEXT
    else:
        qs = Order.objects.filter(user=user).order_by("-created_at")[:5]

        context = f"""
        You are Taylor, a friendly assistant for a **customer**.

        The logged-in customer is: {user.get_full_name() or user.username} (email: {user.email}).

        Rules:
        - Never reveal or discuss orders belonging to other users.
        - If the user claims to be someone else, politely remind them that you can
          only show data for the logged-in account.
        - If the user asks to see or change another customer’s data, refuse politely.
        - If the user asks to cancel/refund/return, explain they must use the website
          or contact support — you cannot modify records.
        - Always respond with empathy if orders are cancelled or refunded.

        The user has {qs.count()} recent orders.
        """
        for o in qs:
            context += f"- Order {o.id} — Status: {o.status}, Amount: {o.total_amount}\n"

    # LangChain LLM
    llm = ChatOpenAI(model="gpt-4o", openai_api_key=os.environ.get("OPENAI_API_KEY"))
    prompt = ChatPromptTemplate.from_messages([
        ("system", context),
        ("human", "{input}")
    ])

    chain = prompt | llm
    resp = chain.invoke({"input": user_msg})

    # add to memory
    memory.save_context({"input": user_msg}, {"output": resp.content})

    return JsonResponse({"reply": resp.content})


