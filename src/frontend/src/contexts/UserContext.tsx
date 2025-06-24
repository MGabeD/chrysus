import React, { createContext, useContext, useState } from "react";

interface User {
  name: string;
}

interface UserContextType {
  selectedUser: User | null;
  setSelectedUser: (user: User | null) => void;
  users: User[];
  setUsers: (users: User[]) => void;
  viewMode: "aggregate" | "transactions" | "tables" | "recommendations";
  setViewMode: (
    mode: "aggregate" | "transactions" | "tables" | "recommendations"
  ) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [viewMode, setViewMode] = useState<
    "aggregate" | "transactions" | "tables" | "recommendations"
  >("aggregate");

  return (
    <UserContext.Provider
      value={{
        selectedUser,
        setSelectedUser,
        users,
        setUsers,
        viewMode,
        setViewMode,
      }}
    >
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
};
