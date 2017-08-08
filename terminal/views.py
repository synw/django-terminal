import json
from django.views.generic.base import TemplateView, View
from django.http.response import Http404
from django.http import JsonResponse
from django.conf import settings
from jobrunner.producers import runjob
from terminal.commands import rprint
from terminal.apps import ALLCMDS


def get_command(name):
    global ALLCMDS
    for app in ALLCMDS:
        cmds = ALLCMDS[app]
        for cmd in cmds:
            if cmd.name == name:
                return cmd, app
    return None, None


class TermView(TemplateView):
    template_name = 'terminal/index.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404
        return super(TermView, self).dispatch(request, *args, **kwargs)


class PostCmdView(View):

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponse({})
        data = json.loads(self.request.body.decode('utf-8'))
        cmdname = data["command"]
        jobid = data["jobid"]
        print(cmdname, "/", jobid)
        if (jobid != ""):
            err = runjob(cmdname, jobid)
            if err is not None:
                rprint("Error posting the job", cmdname, "(", jobid, "):", err)
                return JsonResponse({"error": err})
            return JsonResponse({"ok": 1})
        cargs = []
        if " " in cmdname:
            s = cmdname.split(" ")
            print(s)
            cmdname = s[0]
            cargs = s[1:]
        cmd, _ = get_command(cmdname)
        if cmd is None:
            return JsonResponse({"error": "Command " + cmdname + " not found"})
        argslist = ""
        numargs = len(cargs)
        if numargs > 0:
            for arg in cargs:
                argslist = argslist + " " + arg
        if settings.DEBUG is True:
            print("=> Command", cmdname + argslist,
                  "received from remote terminal")
        err = cmd.run(request, cargs)
        if err is not None:
            rprint("Error running the command", cmdname + ":", err)
            return JsonResponse({"error": err})
        return JsonResponse({"ok": 1})
