// src/pages/AdminPage.tsx
import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";
import HomePage from "./HomePage";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Activity, AlertCircle, HardDrive, Edit, Lock, Plus, RefreshCw, Server, Trash2, User } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { authApi, UserInfo } from "@/api/auth";

export default function AdminPage() {
  const { user, isLoading: authLoading } = useAuth();
  const { toast } = useToast();
  const [tab, setTab] = useState("users");
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [newUserOpen, setNewUserOpen] = useState(false);
  const [creatingUser, setCreatingUser] = useState(false);
  const [editingUser, setEditingUser] = useState<UserInfo | null>(null);
  const [userFormData, setUserFormData] = useState({
    username: "",
    email: "",
    password: "",
    password_confirm: "",
    full_name: "",
    is_active: true,
    is_superuser: false
  });
  
  // Load users
  const loadUsers = useCallback(async (showToast = false) => {
    try {
      setLoading(true);
      // This is a mock implementation since we don't have a real users API endpoint yet
      // In a real app, this would call an API endpoint
      setTimeout(() => {
        const mockUsers: UserInfo[] = [
          {
            id: "1",
            username: "admin",
            email: "admin@example.com",
            full_name: "Admin User",
            is_active: true,
            is_superuser: true,
            created_at: new Date(2023, 0, 1).toISOString()
          },
          {
            id: "2",
            username: "user1",
            email: "user1@example.com",
            full_name: "Regular User",
            is_active: true,
            is_superuser: false,
            created_at: new Date(2023, 1, 15).toISOString()
          },
          {
            id: "3",
            username: "inactive",
            email: "inactive@example.com",
            full_name: "Inactive User",
            is_active: false,
            is_superuser: false,
            created_at: new Date(2023, 2, 20).toISOString()
          }
        ];
        
        setUsers(mockUsers);
        setLoading(false);
        setError("");
        
        if (showToast) {
          toast({
            title: "Users loaded",
            description: `${mockUsers.length} users loaded.`,
            variant: "default",
          });
        }
      }, 1000);
    } catch (err) {
      console.error(err);
      setError("Error loading users");
      setLoading(false);
      
      if (showToast) {
        toast({
          title: "Error",
          description: "Could not load users.",
          variant: "destructive",
        });
      }
    }
  }, [toast]);
  
  // Load users on mount
  useEffect(() => {
    if (tab === "users") {
      loadUsers();
    }
  }, [loadUsers, tab]);
  
  // Handle form input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setUserFormData(prev => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value
    }));
  };
  
  // Handle switch change
  const handleSwitchChange = (name: string, checked: boolean) => {
    setUserFormData(prev => ({
      ...prev,
      [name]: checked
    }));
  };
  
  // Handle form submission for new user
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingUser(true);
    
    // Validate
    if (userFormData.password !== userFormData.password_confirm) {
      toast({
        title: "Passwords don't match",
        description: "Please make sure passwords match.",
        variant: "destructive",
      });
      setCreatingUser(false);
      return;
    }
    
    // In a real app, this would call an API endpoint
    setTimeout(() => {
      toast({
        title: "User created",
        description: `User ${userFormData.username} created successfully.`,
        variant: "default",
      });
      
      setCreatingUser(false);
      setNewUserOpen(false);
      loadUsers();
      
      // Reset form
      setUserFormData({
        username: "",
        email: "",
        password: "",
        password_confirm: "",
        full_name: "",
        is_active: true,
        is_superuser: false
      });
    }, 1000);
  };
  
  // Open edit dialog for user
  const handleEditUser = (user: UserInfo) => {
    setEditingUser(user);
    setUserFormData({
      username: user.username,
      email: user.email,
      password: "",
      password_confirm: "",
      full_name: user.full_name || "",
      is_active: user.is_active,
      is_superuser: user.is_superuser
    });
  };
  
  // Update user
  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingUser(true);
    
    // In a real app, this would call an API endpoint
    setTimeout(() => {
      toast({
        title: "User updated",
        description: `User ${userFormData.username} updated successfully.`,
        variant: "default",
      });
      
      setCreatingUser(false);
      setEditingUser(null);
      loadUsers();
      
      // Reset form
      setUserFormData({
        username: "",
        email: "",
        password: "",
        password_confirm: "",
        full_name: "",
        is_active: true,
        is_superuser: false
      });
    }, 1000);
  };
  
  // Delete user
  const handleDeleteUser = async (user: UserInfo) => {
    // Prevent deleting current user
    if (user.id === "1") {
      toast({
        title: "Cannot delete admin",
        description: "You cannot delete the main admin account.",
        variant: "destructive",
      });
      return;
    }
    
    // In a real app, this would call an API endpoint
    toast({
      title: "User deleted",
      description: `User ${user.username} has been deleted.`,
      variant: "default",
    });
    
    // Update local state to reflect the deletion
    setUsers(prevUsers => prevUsers.filter(u => u.id !== user.id));
  };
  
  // Error state during loading
  if (authLoading) {
    return <div>Loading...</div>;
  }
  
  // Not an admin
  if (!user?.is_superuser) {
    return (
      <HomePage>
        <div className="p-8">
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4 mr-2" />
            <AlertDescription>
              You do not have permission to access the admin panel.
            </AlertDescription>
          </Alert>
          
          <Button onClick={() => (window as any).navigate('/')}>
            Go to Home
          </Button>
        </div>
      </HomePage>
    );
  }

  return (
    <HomePage>
      <div className="p-8 space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold">Admin Panel</h1>
          
          <div className="flex space-x-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => loadUsers(true)} 
              disabled={loading}
            >
              {loading ? (
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Refresh
            </Button>
          </div>
        </div>
        
        <Tabs defaultValue="users" value={tab} onValueChange={setTab}>
          <TabsList className="grid grid-cols-4 w-full sm:w-auto">
            <TabsTrigger value="users">
              <User className="h-4 w-4 mr-2" />
              Users
            </TabsTrigger>
            <TabsTrigger value="models">
              <Server className="h-4 w-4 mr-2" />
              Models
            </TabsTrigger>
            <TabsTrigger value="database">
              <HardDrive className="h-4 w-4 mr-2" />
              Database
            </TabsTrigger>
            <TabsTrigger value="logs">
              <Activity className="h-4 w-4 mr-2" />
              Logs
            </TabsTrigger>
          </TabsList>
          
          {/* Users Tab */}
          <TabsContent value="users">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>User Management</CardTitle>
                  <CardDescription>
                    Manage users, permissions, and API keys
                  </CardDescription>
                </div>
                
                <Button onClick={() => setNewUserOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add User
                </Button>
              </CardHeader>
              
              <CardContent>
                {loading ? (
                  <div className="animate-pulse space-y-3">
                    <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded"></div>
                    <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
                  </div>
                ) : error ? (
                  <div className="text-center py-4">
                    <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
                    <p className="text-gray-500 dark:text-gray-400">{error}</p>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => loadUsers(true)}
                      className="mt-2"
                    >
                      Try again
                    </Button>
                  </div>
                ) : (
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Username</TableHead>
                          <TableHead>Email</TableHead>
                          <TableHead>Full Name</TableHead>
                          <TableHead>Role</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {users.map(user => (
                          <TableRow key={user.id}>
                            <TableCell className="font-medium">{user.username}</TableCell>
                            <TableCell>{user.email}</TableCell>
                            <TableCell>{user.full_name || "-"}</TableCell>
                            <TableCell>
                              {user.is_superuser ? (
                                <Badge>Admin</Badge>
                              ) : (
                                <Badge variant="outline">User</Badge>
                              )}
                            </TableCell>
                            <TableCell>
                              {user.is_active ? (
                                <Badge variant="default" className="bg-green-500">Active</Badge>
                              ) : (
                                <Badge variant="destructive">Inactive</Badge>
                              )}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end space-x-2">
                                <Button 
                                  variant="ghost" 
                                  size="icon"
                                  onClick={() => handleEditUser(user)}
                                >
                                  <Edit className="h-4 w-4" />
                                </Button>
                                <Button 
                                  variant="ghost" 
                                  size="icon"
                                  onClick={() => handleDeleteUser(user)}
                                >
                                  <Trash2 className="h-4 w-4 text-red-500" />
                                </Button>
                                <Button 
                                  variant="ghost" 
                                  size="icon"
                                >
                                  <Lock className="h-4 w-4" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* Other tabs just show placeholders for now */}
          <TabsContent value="models">
            <Card>
              <CardHeader>
                <CardTitle>Model Management</CardTitle>
                <CardDescription>
                  Manage available models and their settings
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-gray-500">
                  Model management features will be implemented in a future update.
                </p>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="database">
            <Card>
              <CardHeader>
                <CardTitle>Database Management</CardTitle>
                <CardDescription>
                  Manage database settings and operations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-gray-500">
                  Database management features will be implemented in a future update.
                </p>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="logs">
            <Card>
              <CardHeader>
                <CardTitle>System Logs</CardTitle>
                <CardDescription>
                  View and analyze system logs
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-gray-500">
                  Log viewing features will be implemented in a future update.
                </p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
      
      {/* New User Dialog */}
      <Dialog open={newUserOpen} onOpenChange={setNewUserOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Create New User</DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleCreateUser}>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="username" className="text-right">
                  Username
                </Label>
                <Input
                  id="username"
                  name="username"
                  className="col-span-3"
                  value={userFormData.username}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="email" className="text-right">
                  Email
                </Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  className="col-span-3"
                  value={userFormData.email}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="password" className="text-right">
                  Password
                </Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  className="col-span-3"
                  value={userFormData.password}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="password_confirm" className="text-right">
                  Confirm
                </Label>
                <Input
                  id="password_confirm"
                  name="password_confirm"
                  type="password"
                  className="col-span-3"
                  value={userFormData.password_confirm}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="full_name" className="text-right">
                  Full Name
                </Label>
                <Input
                  id="full_name"
                  name="full_name"
                  className="col-span-3"
                  value={userFormData.full_name}
                  onChange={handleInputChange}
                />
              </div>
              
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right">
                  Is Active
                </Label>
                <div className="flex items-center space-x-2 col-span-3">
                  <Switch
                    id="is_active"
                    name="is_active"
                    checked={userFormData.is_active}
                    onCheckedChange={(checked) => handleSwitchChange("is_active", checked)}
                  />
                  <Label htmlFor="is_active">
                    {userFormData.is_active ? "Active" : "Inactive"}
                  </Label>
                </div>
              </div>
              
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right">
                  Is Admin
                </Label>
                <div className="flex items-center space-x-2 col-span-3">
                  <Switch
                    id="is_superuser"
                    name="is_superuser"
                    checked={userFormData.is_superuser}
                    onCheckedChange={(checked) => handleSwitchChange("is_superuser", checked)}
                  />
                  <Label htmlFor="is_superuser">
                    {userFormData.is_superuser ? "Admin" : "Regular User"}
                  </Label>
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setNewUserOpen(false)} type="button">
                Cancel
              </Button>
              <Button type="submit" disabled={creatingUser}>
                {creatingUser ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create User"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
      
      {/* Edit User Dialog */}
      <Dialog open={!!editingUser} onOpenChange={(open) => !open && setEditingUser(null)}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Edit User: {editingUser?.username}</DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleUpdateUser}>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit_email" className="text-right">
                  Email
                </Label>
                <Input
                  id="edit_email"
                  name="email"
                  type="email"
                  className="col-span-3"
                  value={userFormData.email}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit_full_name" className="text-right">
                  Full Name
                </Label>
                <Input
                  id="edit_full_name"
                  name="full_name"
                  className="col-span-3"
                  value={userFormData.full_name}
                  onChange={handleInputChange}
                />
              </div>
              
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right">
                  Is Active
                </Label>
                <div className="flex items-center space-x-2 col-span-3">
                  <Switch
                    id="edit_is_active"
                    checked={userFormData.is_active}
                    onCheckedChange={(checked) => handleSwitchChange("is_active", checked)}
                  />
                  <Label htmlFor="edit_is_active">
                    {userFormData.is_active ? "Active" : "Inactive"}
                  </Label>
                </div>
              </div>
              
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right">
                  Is Admin
                </Label>
                <div className="flex items-center space-x-2 col-span-3">
                  <Switch
                    id="edit_is_superuser"
                    checked={userFormData.is_superuser}
                    onCheckedChange={(checked) => handleSwitchChange("is_superuser", checked)}
                  />
                  <Label htmlFor="edit_is_superuser">
                    {userFormData.is_superuser ? "Admin" : "Regular User"}
                  </Label>
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditingUser(null)} type="button">
                Cancel
              </Button>
              <Button type="submit" disabled={creatingUser}>
                {creatingUser ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Updating...
                  </>
                ) : (
                  "Update User"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </HomePage>
  );
}