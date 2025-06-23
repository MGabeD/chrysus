import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useUser } from "@/contexts/UserContext";
import { Loader2, Users, User } from "lucide-react";
import { buildApiUrl } from "@/lib/config";

export const UserList = () => {
  const { selectedUser, setSelectedUser, users, setUsers } = useUser();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, [setUsers]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch(buildApiUrl("users"));
      if (response.ok) {
        const data = await response.json();
        const userList = data.users.map((name: string) => ({ name }));
        setUsers(userList);
      }
    } catch (error) {
      console.error("Failed to fetch users:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleUserSelect = (user: { name: string }) => {
    setSelectedUser(user);
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Users
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="w-5 h-5" />
          Users ({users.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {users.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No users available</p>
          ) : (
            users.map((user) => (
              <button
                key={user.name}
                onClick={() => handleUserSelect(user)}
                className={`w-full text-left p-3 rounded-lg border transition-all hover:bg-gray-50 ${
                  selectedUser?.name === user.name
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-gray-200"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2 rounded-full ${
                      selectedUser?.name === user.name
                        ? "bg-blue-100"
                        : "bg-gray-100"
                    }`}
                  >
                    <User className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="font-medium">{user.name}</div>
                    <div className="text-sm text-gray-500">
                      Financial Data Available
                    </div>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
};
