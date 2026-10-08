import { useEffect, useState } from "react";
import { notificationsApi, announcementsApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function ParentNotifications() {
  const [notes, setNotes] = useState([]);
  const [anns, setAnns] = useState([]);
  useEffect(() => {
    notificationsApi.list().then(setNotes);
    announcementsApi.list().then(setAnns);
  }, []);

  return (
    <div data-testid="parent-notifications" className="space-y-8">
      <div>
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Alerts</div>
        <h1 className="font-display font-bold text-3xl tracking-tight mt-1">Notifications</h1>
      </div>

      <Card className="en-card p-6">
        <h3 className="font-display font-semibold text-lg mb-4">Your alerts</h3>
        <div className="space-y-2">
          {notes.map(n => (
            <div key={n.id} className="p-3 rounded-xl border border-border flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">{n.message}</div>
                <div className="text-xs text-muted-foreground mt-0.5">{n.created_at?.slice(0,16).replace("T"," ")}</div>
              </div>
              <Badge variant={n.read ? "outline" : "secondary"} className="rounded-full">{n.type}</Badge>
            </div>
          ))}
          {notes.length === 0 && <div className="text-sm text-muted-foreground">No notifications yet.</div>}
        </div>
      </Card>

      <Card className="en-card p-6">
        <h3 className="font-display font-semibold text-lg mb-4">Announcements</h3>
        <div className="space-y-2">
          {anns.map(a => (
            <div key={a.id} className="p-3 rounded-xl border border-border">
              <div className="font-medium">{a.title}</div>
              <div className="text-sm text-muted-foreground mt-1">{a.body}</div>
            </div>
          ))}
          {anns.length === 0 && <div className="text-sm text-muted-foreground">No announcements yet.</div>}
        </div>
      </Card>
    </div>
  );
}
