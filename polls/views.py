from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.test import TestCase

from .models import Choice, Question


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"
    # OG CODE
    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[
            :5
        ]
    #EXERCISE CODE
    def render_to_response(self,context, **response_kwargs):
        #was cookie sent?
        context["returning_visitor"] = self.request.COOKIES.get("visited_polls") == "yes"
        response = super().render_to_response(context, **response_kwargs)

        # set the cookie
        response.set_cookie("visited_polls", "yes", max_age=120)
        return response
    #SESSION VISIT COUNTER
    def get_context_data(self, **kwargs):
        # VISIT COUNT
        context = super().get_context_data(**kwargs)
        visit_count = self.request.session.get("visit_count", 0)
        visit_count+= 1
        self.request.session["visit_count"] = visit_count
        context["visit_count"] = visit_count
        #POLLS VISITED LAST
        last_poll = None
        last_poll_id = self.request.session.get("last_poll")
        if last_poll_id is not None:
            last_poll = Question.objects.filter(
                pk=last_poll_id, pub_date__lte=timezone.now()
            ).first()
        context["last_poll"] = last_poll
        return context


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"
    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())
    # LAST POLL VIEWED
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        self.request.session["last_poll"] = obj.pk
        return obj



class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))
class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text="Future question.", days=5)
        url = reverse("polls:detail", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        past_question = create_question(question_text="Past Question.", days=-5)
        url = reverse("polls:detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)