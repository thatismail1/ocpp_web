import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import api from '../utils/api';
import { Users, UserPlus, Edit, Trash2, RotateCcw, AlertTriangle } from 'lucide-react';
import { useToast } from '../hooks/use-toast';

const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editUser, setEditUser] = useState(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);
  const { toast } = useToast();

  const [newUser, setNewUser] = useState({
    id_tag: '',
    header_name: '',
    surname: '',
    plan: 'limited',
    quota_kwh: 100,
  });

  const fetchUsers = async () => {
    try {
      const response = await api.get('/api/users');
      setUsers(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch users',
        variant: 'destructive',
      });
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
    const interval = setInterval(fetchUsers, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleAddUser = async () => {
    try {
      await api.post('/api/users', newUser);
      toast({
        title: 'Success',
        description: 'User added successfully',
      });
      setShowAddDialog(false);
      setNewUser({
        id_tag: '',
        header_name: '',
        surname: '',
        plan: 'limited',
        quota_kwh: 100,
      });
      fetchUsers();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to add user',
        variant: 'destructive',
      });
    }
  };

  const handleUpdateUser = async () => {
    try {
      await api.put(`/api/users/${editUser.id_tag}`, {
        header_name: editUser.header_name,
        surname: editUser.surname,
        plan: editUser.plan,
        quota_kwh: editUser.quota_kwh,
      });
      toast({
        title: 'Success',
        description: 'User updated successfully',
      });
      setShowEditDialog(false);
      setEditUser(null);
      fetchUsers();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update user',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteUser = async () => {
    try {
      await api.delete(`/api/users/${userToDelete}`);
      toast({
        title: 'Success',
        description: 'User deleted successfully',
      });
      setShowDeleteDialog(false);
      setUserToDelete(null);
      fetchUsers();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete user',
        variant: 'destructive',
      });
    }
  };

  const handleResetUser = async (idTag) => {
    try {
      await api.post(`/api/users/${idTag}/reset`);
      toast({
        title: 'Success',
        description: 'User usage reset successfully',
      });
      fetchUsers();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to reset user',
        variant: 'destructive',
      });
    }
  };

  const getQuotaPercentage = (user) => {
    if (user.unlimited || !user.quota_kwh) return 0;
    return Math.min((user.used_kwh / user.quota_kwh) * 100, 100);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-600 dark:text-slate-400">Loading users...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="users-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Users className="h-6 w-6 text-slate-600 dark:text-slate-400" />
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">User Management</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">Manage user quotas and charging permissions</p>
          </div>
        </div>
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button className="bg-emerald-600 hover:bg-emerald-700" data-testid="add-user-button">
              <UserPlus className="h-4 w-4 mr-2" />
              Add User
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New User</DialogTitle>
              <DialogDescription>Create a new user with charging quota settings</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="id_tag">RFID Tag</Label>
                <Input
                  id="id_tag"
                  value={newUser.id_tag}
                  onChange={(e) => setNewUser({ ...newUser, id_tag: e.target.value })}
                  placeholder="RFID001"
                  data-testid="add-user-id-tag-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="header_name">First Name</Label>
                  <Input
                    id="header_name"
                    value={newUser.header_name}
                    onChange={(e) => setNewUser({ ...newUser, header_name: e.target.value })}
                    placeholder="John"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="surname">Last Name</Label>
                  <Input
                    id="surname"
                    value={newUser.surname}
                    onChange={(e) => setNewUser({ ...newUser, surname: e.target.value })}
                    placeholder="Doe"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="plan">Plan Type</Label>
                <Select value={newUser.plan} onValueChange={(value) => setNewUser({ ...newUser, plan: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="limited">Limited</SelectItem>
                    <SelectItem value="unlimited">Unlimited</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {newUser.plan === 'limited' && (
                <div className="space-y-2">
                  <Label htmlFor="quota_kwh">Quota (kWh)</Label>
                  <Input
                    id="quota_kwh"
                    type="number"
                    value={newUser.quota_kwh}
                    onChange={(e) => setNewUser({ ...newUser, quota_kwh: parseFloat(e.target.value) })}
                  />
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAddDialog(false)}>Cancel</Button>
              <Button onClick={handleAddUser} data-testid="confirm-add-user-button">Add User</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Users Table */}
      <Card className="border-slate-200 dark:border-slate-800">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>RFID Tag</TableHead>
                <TableHead>Plan</TableHead>
                <TableHead>Quota</TableHead>
                <TableHead>Used</TableHead>
                <TableHead>Remaining</TableHead>
                <TableHead>Usage</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => {
                const percentage = getQuotaPercentage(user);
                const isNearLimit = percentage > 80 && !user.unlimited;

                return (
                  <TableRow key={user.id_tag}>
                    <TableCell className="font-medium">{user.full_name}</TableCell>
                    <TableCell>
                      <code className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                        {user.id_tag}
                      </code>
                    </TableCell>
                    <TableCell>
                      <Badge variant={user.unlimited ? 'default' : 'secondary'}>
                        {user.plan}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {user.unlimited ? '∞' : `${user.quota_kwh} kWh`}
                    </TableCell>
                    <TableCell>{user.used_kwh.toFixed(2)} kWh</TableCell>
                    <TableCell>
                      {user.unlimited ? '∞' : (
                        <span className={isNearLimit ? 'text-amber-600 dark:text-amber-400 font-semibold' : ''}>
                          {user.remaining_kwh?.toFixed(2) || 0} kWh
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      {!user.unlimited ? (
                        <div className="flex items-center space-x-2">
                          <Progress value={percentage} className="w-24" />
                          <span className="text-xs text-slate-600 dark:text-slate-400">
                            {percentage.toFixed(0)}%
                          </span>
                        </div>
                      ) : (
                        <span className="text-sm text-slate-500">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setEditUser(user);
                            setShowEditDialog(true);
                          }}
                          data-testid={`edit-user-${user.id_tag}`}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleResetUser(user.id_tag)}
                          data-testid={`reset-user-${user.id_tag}`}
                        >
                          <RotateCcw className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setUserToDelete(user.id_tag);
                            setShowDeleteDialog(true);
                          }}
                          data-testid={`delete-user-${user.id_tag}`}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
            <DialogDescription>Update user information and quota settings</DialogDescription>
          </DialogHeader>
          {editUser && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="edit_header_name">First Name</Label>
                  <Input
                    id="edit_header_name"
                    value={editUser.header_name}
                    onChange={(e) => setEditUser({ ...editUser, header_name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit_surname">Last Name</Label>
                  <Input
                    id="edit_surname"
                    value={editUser.surname}
                    onChange={(e) => setEditUser({ ...editUser, surname: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit_plan">Plan Type</Label>
                <Select value={editUser.plan} onValueChange={(value) => setEditUser({ ...editUser, plan: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="limited">Limited</SelectItem>
                    <SelectItem value="unlimited">Unlimited</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {editUser.plan === 'limited' && (
                <div className="space-y-2">
                  <Label htmlFor="edit_quota_kwh">Quota (kWh)</Label>
                  <Input
                    id="edit_quota_kwh"
                    type="number"
                    value={editUser.quota_kwh || 0}
                    onChange={(e) => setEditUser({ ...editUser, quota_kwh: parseFloat(e.target.value) })}
                  />
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>Cancel</Button>
            <Button onClick={handleUpdateUser} data-testid="confirm-edit-user-button">Update User</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <span>Confirm Deletion</span>
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this user? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>Cancel</Button>
            <Button
              onClick={handleDeleteUser}
              data-testid="confirm-delete-user-button"
              className="bg-red-600 hover:bg-red-700"
            >
              Delete User
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UsersPage;