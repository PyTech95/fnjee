import { useEffect, useState } from "react";
import { usersApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export default function AdminStudents() {
  const [role, setRole] = useState("student");
  const [rows, setRows] = useState([]);
  useEffect(() => { usersApi.list(role).then(setRows); }, [role]);

  return (
    <div data-testid="admin-users-page" className="space-y-6">
      <div>
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-primary">People</div>
        <h1 className="font-display font-bold text-3xl tracking-tight mt-1">Users</h1>
      </div>
      <Tabs value={role} onValueChange={setRole}>
        <TabsList className="rounded-full">
          <TabsTrigger value="student" className="rounded-full">Students</TabsTrigger>
          <TabsTrigger value="parent" className="rounded-full">Parents</TabsTrigger>
          <TabsTrigger value="admin" className="rounded-full">Admins</TabsTrigger>
        </TabsList>
      </Tabs>

      <Card className="en-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Email</TableHead>
              {role === "student" && <TableHead>Target</TableHead>}
              {role === "student" && <TableHead className="text-right">Coins</TableHead>}
              {role === "student" && <TableHead className="text-right">Streak</TableHead>}
              {role === "parent" && <TableHead>Children</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map(u => (
              <TableRow key={u.id}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <Avatar className="h-8 w-8"><AvatarImage src={u.avatar} /><AvatarFallback>{u.name?.[0]}</AvatarFallback></Avatar>
                    <div className="font-medium">{u.name}</div>
                  </div>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">{u.email}</TableCell>
                {role === "student" && <TableCell><Badge variant="secondary" className="rounded-full">{u.exam_target || "—"}</Badge></TableCell>}
                {role === "student" && <TableCell className="text-right font-medium">{u.reward_coins}</TableCell>}
                {role === "student" && <TableCell className="text-right">{u.streak_days}</TableCell>}
                {role === "parent" && <TableCell>{u.child_ids?.length || 0}</TableCell>}
              </TableRow>
            ))}
            {rows.length === 0 && <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground py-8">No {role}s yet.</TableCell></TableRow>}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
